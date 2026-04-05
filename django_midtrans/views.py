import logging

from rest_framework import generics, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet

from django_midtrans.constants import PaymentType
from django_midtrans.exceptions import MidtransError
from django_midtrans.models import (
    MidtransInvoice,
    MidtransPayment,
    MidtransSubscription,
)
from django_midtrans.notification import NotificationHandler
from django_midtrans.serializers import (
    ChargeSerializer,
    CreateInvoiceSerializer,
    CreateSubscriptionSerializer,
    InvoiceSerializer,
    PaymentListSerializer,
    PaymentSerializer,
    RefundInputSerializer,
    RefundSerializer,
    SubscriptionSerializer,
    VoidInvoiceSerializer,
)
from django_midtrans.services import InvoiceService, PaymentService, SubscriptionService

logger = logging.getLogger("django_midtrans")


# ─── Payment Views ──────────────────────────────────────

class ChargeView(APIView):
    """Create a new payment charge via Midtrans Core API."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChargeSerializer(data=request.data)
        serializer.validate_and_raise = True
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        service = PaymentService()

        # Build payment options from flat fields
        payment_options = {}
        if data["payment_type"] == PaymentType.CREDIT_CARD:
            payment_options["token_id"] = data.get("token_id", "")
        elif data["payment_type"] == PaymentType.BANK_TRANSFER:
            payment_options["bank"] = data.get("bank", "bca")
        elif data["payment_type"] in [PaymentType.GOPAY, PaymentType.SHOPEEPAY]:
            if callback_url := data.get("callback_url"):
                payment_options["callback_url"] = callback_url
        elif data["payment_type"] == PaymentType.QRIS:
            payment_options["acquirer"] = data.get("qris_acquirer", "gopay")
        elif data["payment_type"] == PaymentType.CSTORE:
            payment_options["store"] = data.get("store", "indomaret")

        try:
            payment, response = service.create_charge(
                payment_type=data["payment_type"],
                gross_amount=data["gross_amount"],
                order_id=data.get("order_id"),
                customer_details=data.get("customer_details"),
                item_details=data.get("item_details"),
                payment_options=payment_options,
                custom_expiry=data.get("custom_expiry"),
                notification_url=data.get("notification_url"),
                metadata=data.get("metadata"),
                custom_fields=data.get("custom_fields"),
                user=request.user if request.user.is_authenticated else None,
            )
        except MidtransError as e:
            return Response(
                {"error": str(e), "data": e.data},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            PaymentSerializer(payment).data,
            status=status.HTTP_201_CREATED,
        )


class PaymentViewSet(ReadOnlyModelViewSet):
    """View and manage payments."""

    permission_classes = [IsAuthenticated]
    lookup_field = "pk"

    def get_serializer_class(self):
        if self.action == "list":
            return PaymentListSerializer
        return PaymentSerializer

    def get_queryset(self):
        qs = MidtransPayment.objects.all()
        if not self.request.user.is_staff:
            qs = qs.filter(user=self.request.user)

        # Filtering
        payment_type = self.request.query_params.get("payment_type")
        if payment_type:
            qs = qs.filter(payment_type=payment_type)

        transaction_status = self.request.query_params.get("status")
        if transaction_status:
            qs = qs.filter(transaction_status=transaction_status)

        return qs.prefetch_related("items")

    @action(detail=True, methods=["get"])
    def check_status(self, request, pk=None):
        payment = self.get_object()
        service = PaymentService()
        try:
            response = service.get_status(payment)
        except MidtransError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            "payment": PaymentSerializer(payment).data,
            "midtrans_response": response,
        })

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        payment = self.get_object()
        if payment.is_final:
            return Response({"error": "Payment is already in a final state."}, status=status.HTTP_400_BAD_REQUEST)

        service = PaymentService()
        try:
            payment, response = service.cancel_payment(payment)
        except MidtransError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(PaymentSerializer(payment).data)

    @action(detail=True, methods=["post"])
    def expire(self, request, pk=None):
        payment = self.get_object()
        if not payment.is_pending:
            return Response({"error": "Only pending payments can be expired."}, status=status.HTTP_400_BAD_REQUEST)

        service = PaymentService()
        try:
            payment, response = service.expire_payment(payment)
        except MidtransError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(PaymentSerializer(payment).data)

    @action(detail=True, methods=["post"])
    def refund(self, request, pk=None):
        payment = self.get_object()
        if not payment.is_paid:
            return Response({"error": "Only paid payments can be refunded."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = RefundInputSerializer(data=request.data, context={"payment": payment})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        service = PaymentService()
        try:
            payment, refund, response = service.refund_payment(
                payment,
                amount=data["amount"],
                reason=data.get("reason", ""),
                direct=data.get("direct", False),
            )
        except MidtransError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "payment": PaymentSerializer(payment).data,
            "refund": RefundSerializer(refund).data,
        })

    @action(detail=True, methods=["post"])
    def capture(self, request, pk=None):
        payment = self.get_object()
        if payment.payment_type != PaymentType.CREDIT_CARD:
            return Response({"error": "Capture is only for credit card payments."}, status=status.HTTP_400_BAD_REQUEST)

        amount = request.data.get("amount")
        service = PaymentService()
        try:
            payment, response = service.capture_payment(payment, amount=amount)
        except MidtransError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(PaymentSerializer(payment).data)


# ─── Notification View ──────────────────────────────────

class NotificationView(APIView):
    """
    Midtrans webhook notification handler.
    Must be publicly accessible (no auth required).
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        handler = NotificationHandler()
        notification = handler.handle(request.data)
        return Response({"status": "ok", "notification_id": str(notification.id)})


# ─── Invoice Views ──────────────────────────────────────

class InvoiceListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = InvoiceSerializer

    def get_queryset(self):
        qs = MidtransInvoice.objects.all()
        if not self.request.user.is_staff:
            qs = qs.filter(user=self.request.user)
        return qs.prefetch_related("items")

    def create(self, request, *args, **kwargs):
        serializer = CreateInvoiceSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        service = InvoiceService()
        try:
            invoice, response = service.create_invoice(
                customer_name=data["customer_name"],
                customer_email=data["customer_email"],
                due_date=data["due_date"],
                items=data["items"],
                customer_phone=data.get("customer_phone", ""),
                customer_id=data.get("customer_id", ""),
                notes=data.get("notes", ""),
                order_id=data.get("order_id"),
                invoice_number=data.get("invoice_number"),
                user=request.user if request.user.is_authenticated else None,
                metadata=data.get("metadata"),
            )
        except MidtransError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(InvoiceSerializer(invoice).data, status=status.HTTP_201_CREATED)


class InvoiceDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = InvoiceSerializer

    def get_queryset(self):
        qs = MidtransInvoice.objects.all()
        if not self.request.user.is_staff:
            qs = qs.filter(user=self.request.user)
        return qs.prefetch_related("items")


class InvoiceVoidView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            invoice = MidtransInvoice.objects.get(pk=pk)
        except MidtransInvoice.DoesNotExist:
            return Response({"error": "Invoice not found."}, status=status.HTTP_404_NOT_FOUND)

        if not request.user.is_staff and invoice.user != request.user:
            return Response({"error": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        serializer = VoidInvoiceSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        service = InvoiceService()
        try:
            invoice, response = service.void_invoice(invoice, reason=serializer.validated_data.get("reason", ""))
        except MidtransError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(InvoiceSerializer(invoice).data)


# ─── Subscription Views ─────────────────────────────────

class SubscriptionListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SubscriptionSerializer

    def get_queryset(self):
        qs = MidtransSubscription.objects.all()
        if not self.request.user.is_staff:
            qs = qs.filter(user=self.request.user)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = CreateSubscriptionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        service = SubscriptionService()
        try:
            subscription, response = service.create_subscription(
                name=data["name"],
                amount=data["amount"],
                payment_type=data["payment_type"],
                token=data.get("token", ""),
                interval=data.get("interval", 1),
                interval_unit=data.get("interval_unit", "month"),
                max_interval=data.get("max_interval", 12),
                start_time=data.get("start_time"),
                retry_interval=data.get("retry_interval", 1),
                retry_interval_unit=data.get("retry_interval_unit", "day"),
                retry_max_interval=data.get("retry_max_interval", 3),
                customer_details=data.get("customer_details"),
                gopay_account_id=data.get("gopay_account_id", ""),
                user=request.user if request.user.is_authenticated else None,
                metadata=data.get("metadata"),
            )
        except MidtransError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(SubscriptionSerializer(subscription).data, status=status.HTTP_201_CREATED)


class SubscriptionDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SubscriptionSerializer

    def get_queryset(self):
        qs = MidtransSubscription.objects.all()
        if not self.request.user.is_staff:
            qs = qs.filter(user=self.request.user)
        return qs


class SubscriptionActionView(APIView):
    """Disable, enable, or cancel a subscription."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk, action_name):
        try:
            subscription = MidtransSubscription.objects.get(pk=pk)
        except MidtransSubscription.DoesNotExist:
            return Response({"error": "Subscription not found."}, status=status.HTTP_404_NOT_FOUND)

        if not request.user.is_staff and subscription.user != request.user:
            return Response({"error": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        service = SubscriptionService()
        action_map = {
            "disable": service.disable_subscription,
            "enable": service.enable_subscription,
            "cancel": service.cancel_subscription,
        }

        handler = action_map.get(action_name)
        if not handler:
            return Response({"error": "Invalid action."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            subscription, response = handler(subscription)
        except MidtransError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(SubscriptionSerializer(subscription).data)
