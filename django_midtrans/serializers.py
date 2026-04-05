from decimal import Decimal

from rest_framework import serializers

from django_midtrans.constants import BankType, PaymentType
from django_midtrans.models import (
    MidtransInvoice,
    MidtransInvoiceItem,
    MidtransNotification,
    MidtransPayment,
    MidtransPaymentItem,
    MidtransRefund,
    MidtransSubscription,
)


# ─── Payment ────────────────────────────────────────────

class PaymentItemSerializer(serializers.ModelSerializer):
    subtotal = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)

    class Meta:
        model = MidtransPaymentItem
        fields = ["id", "item_id", "name", "price", "quantity", "brand", "category", "merchant_name", "url", "subtotal"]
        read_only_fields = ["id"]


class PaymentSerializer(serializers.ModelSerializer):
    items = PaymentItemSerializer(many=True, read_only=True)
    is_paid = serializers.BooleanField(read_only=True)
    is_pending = serializers.BooleanField(read_only=True)
    is_failed = serializers.BooleanField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    net_amount = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)

    class Meta:
        model = MidtransPayment
        fields = [
            "id", "order_id", "transaction_id", "payment_type", "bank",
            "gross_amount", "currency", "transaction_status", "fraud_status",
            "status_code", "status_message",
            "customer_first_name", "customer_last_name", "customer_email", "customer_phone",
            "va_number", "bill_key", "biller_code", "payment_code",
            "redirect_url", "deeplink_url", "qr_string",
            "transaction_time", "settlement_time", "expiry_time",
            "refund_amount", "net_amount",
            "metadata", "custom_field1", "custom_field2", "custom_field3",
            "items", "is_paid", "is_pending", "is_failed", "is_expired",
            "created_at", "updated_at",
        ]
        read_only_fields = fields


class PaymentListSerializer(serializers.ModelSerializer):
    is_paid = serializers.BooleanField(read_only=True)

    class Meta:
        model = MidtransPayment
        fields = [
            "id", "order_id", "payment_type", "gross_amount",
            "transaction_status", "customer_email", "is_paid",
            "created_at",
        ]


class ItemDetailInputSerializer(serializers.Serializer):
    id = serializers.CharField(required=False, default="")
    name = serializers.CharField(max_length=50)
    price = serializers.IntegerField(min_value=0)
    quantity = serializers.IntegerField(min_value=1, default=1)
    brand = serializers.CharField(required=False, default="")
    category = serializers.CharField(required=False, default="")
    merchant_name = serializers.CharField(required=False, default="")
    url = serializers.URLField(required=False, default="")


class CustomerDetailInputSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=255, required=False, default="")
    last_name = serializers.CharField(max_length=255, required=False, default="")
    email = serializers.EmailField(required=False, default="")
    phone = serializers.CharField(max_length=255, required=False, default="")


class CustomExpiryInputSerializer(serializers.Serializer):
    expiry_duration = serializers.IntegerField(min_value=1)
    unit = serializers.ChoiceField(choices=["second", "minute", "hour", "day"], default="minute")


class ChargeSerializer(serializers.Serializer):
    payment_type = serializers.ChoiceField(choices=[c[0] for c in PaymentType.CHOICES])
    gross_amount = serializers.IntegerField(min_value=1)
    order_id = serializers.CharField(max_length=50, required=False)

    # Payment type specific
    bank = serializers.ChoiceField(choices=[c[0] for c in BankType.CHOICES], required=False)
    token_id = serializers.CharField(required=False, help_text="Credit card token from frontend tokenization")
    callback_url = serializers.URLField(required=False)
    store = serializers.ChoiceField(choices=["indomaret", "alfamart"], required=False)
    qris_acquirer = serializers.ChoiceField(choices=["gopay", "airpay"], required=False, default="gopay")

    # Optional details
    customer_details = CustomerDetailInputSerializer(required=False)
    item_details = ItemDetailInputSerializer(many=True, required=False)
    custom_expiry = CustomExpiryInputSerializer(required=False)
    notification_url = serializers.URLField(required=False)
    metadata = serializers.DictField(required=False)
    custom_fields = serializers.ListField(child=serializers.CharField(max_length=255), max_length=3, required=False)

    def validate(self, attrs):
        payment_type = attrs.get("payment_type")

        if payment_type == PaymentType.CREDIT_CARD and not attrs.get("token_id"):
            raise serializers.ValidationError({"token_id": "Required for credit card payments."})

        if payment_type == PaymentType.BANK_TRANSFER and not attrs.get("bank"):
            raise serializers.ValidationError({"bank": "Required for bank transfer payments."})

        if payment_type == PaymentType.CSTORE and not attrs.get("store"):
            raise serializers.ValidationError({"store": "Required for convenience store payments."})

        # Validate item totals
        items = attrs.get("item_details", [])
        if items:
            total = sum(item["price"] * item.get("quantity", 1) for item in items)
            if total != attrs["gross_amount"]:
                raise serializers.ValidationError(
                    {"item_details": f"Sum of items ({total}) must equal gross_amount ({attrs['gross_amount']})."}
                )

        return attrs


# ─── Refund ─────────────────────────────────────────────

class RefundSerializer(serializers.ModelSerializer):
    class Meta:
        model = MidtransRefund
        fields = [
            "id", "refund_key", "amount", "reason", "is_direct",
            "status", "status_code", "status_message",
            "created_at",
        ]
        read_only_fields = fields


class RefundInputSerializer(serializers.Serializer):
    amount = serializers.IntegerField(min_value=1)
    reason = serializers.CharField(max_length=255, required=False, default="")
    direct = serializers.BooleanField(default=False)

    def validate_amount(self, value):
        payment = self.context.get("payment")
        if payment and value > payment.net_amount:
            raise serializers.ValidationError("Refund amount exceeds remaining payment amount.")
        return value


# ─── Notification ───────────────────────────────────────

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = MidtransNotification
        fields = [
            "id", "order_id", "transaction_id", "transaction_status",
            "fraud_status", "payment_type", "status_code", "gross_amount",
            "status", "error_message", "created_at",
        ]
        read_only_fields = fields


class NotificationInputSerializer(serializers.Serializer):
    order_id = serializers.CharField()
    transaction_status = serializers.CharField()
    status_code = serializers.CharField()
    gross_amount = serializers.CharField()
    signature_key = serializers.CharField()
    transaction_id = serializers.CharField(required=False, default="")
    fraud_status = serializers.CharField(required=False, default="")
    payment_type = serializers.CharField(required=False, default="")


# ─── Invoice ────────────────────────────────────────────

class InvoiceItemSerializer(serializers.ModelSerializer):
    subtotal = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)

    class Meta:
        model = MidtransInvoiceItem
        fields = ["id", "item_id", "description", "quantity", "price", "subtotal"]
        read_only_fields = ["id"]


class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True, read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = MidtransInvoice
        fields = [
            "id", "invoice_number", "order_id", "midtrans_invoice_id",
            "status", "customer_name", "customer_email", "customer_phone",
            "customer_id", "total_amount", "currency", "due_date",
            "paid_at", "notes", "void_reason", "items",
            "is_overdue", "metadata", "created_at", "updated_at",
        ]
        read_only_fields = fields


class InvoiceItemInputSerializer(serializers.Serializer):
    item_id = serializers.CharField(required=False, default="")
    description = serializers.CharField(max_length=255)
    quantity = serializers.IntegerField(min_value=1, default=1)
    price = serializers.IntegerField(min_value=0)


class CreateInvoiceSerializer(serializers.Serializer):
    customer_name = serializers.CharField(max_length=255)
    customer_email = serializers.EmailField()
    customer_phone = serializers.CharField(max_length=50, required=False, default="")
    customer_id = serializers.CharField(max_length=50, required=False, default="")
    due_date = serializers.DateField()
    items = InvoiceItemInputSerializer(many=True, min_length=1)
    notes = serializers.CharField(required=False, default="")
    order_id = serializers.CharField(max_length=50, required=False)
    invoice_number = serializers.CharField(max_length=50, required=False)
    metadata = serializers.DictField(required=False)


class VoidInvoiceSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=255, required=False, default="")


# ─── Subscription ───────────────────────────────────────

class SubscriptionSerializer(serializers.ModelSerializer):
    schedule_display = serializers.CharField(read_only=True)

    class Meta:
        model = MidtransSubscription
        fields = [
            "id", "midtrans_subscription_id", "name",
            "payment_type", "amount", "currency",
            "interval", "interval_unit", "max_interval", "start_time",
            "current_interval", "status",
            "customer_first_name", "customer_last_name", "customer_email",
            "customer_phone", "schedule_display", "metadata",
            "created_at", "updated_at",
        ]
        read_only_fields = fields


class CreateSubscriptionSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    amount = serializers.IntegerField(min_value=1)
    payment_type = serializers.ChoiceField(choices=[PaymentType.CREDIT_CARD, PaymentType.GOPAY])
    token = serializers.CharField(required=False, default="")
    gopay_account_id = serializers.CharField(required=False, default="")
    interval = serializers.IntegerField(min_value=1, default=1)
    interval_unit = serializers.ChoiceField(choices=["day", "week", "month"], default="month")
    max_interval = serializers.IntegerField(min_value=1, default=12)
    start_time = serializers.DateTimeField(required=False)
    retry_interval = serializers.IntegerField(min_value=1, default=1)
    retry_interval_unit = serializers.ChoiceField(choices=["day", "week", "month"], default="day")
    retry_max_interval = serializers.IntegerField(min_value=1, default=3)
    customer_details = CustomerDetailInputSerializer(required=False)
    metadata = serializers.DictField(required=False)

    def validate(self, attrs):
        payment_type = attrs.get("payment_type")
        if payment_type == PaymentType.CREDIT_CARD and not attrs.get("token"):
            raise serializers.ValidationError({"token": "Required for credit card subscriptions."})
        if payment_type == PaymentType.GOPAY and not attrs.get("gopay_account_id"):
            raise serializers.ValidationError({"gopay_account_id": "Required for GoPay subscriptions."})
        return attrs
