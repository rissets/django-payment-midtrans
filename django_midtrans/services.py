import logging
import uuid
from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from django_midtrans.app_settings import midtrans_settings
from django_midtrans.client import MidtransClient, get_client
from django_midtrans.constants import (
    FraudStatus,
    PaymentType,
    TransactionStatus,
)
from django_midtrans.models import MidtransPayment, MidtransPaymentItem, MidtransRefund

logger = logging.getLogger("django_midtrans")


class PaymentService:
    """
    High-level service for creating and managing Midtrans payments.
    Override methods in subclasses for custom behavior.
    """

    def __init__(self, client: MidtransClient = None):
        self.client = client or get_client()

    # ─── Charge ─────────────────────────────────────────────

    def create_charge(
        self,
        payment_type,
        gross_amount,
        order_id=None,
        customer_details=None,
        item_details=None,
        payment_options=None,
        custom_expiry=None,
        notification_url=None,
        metadata=None,
        custom_fields=None,
        user=None,
    ):
        order_id = order_id or self._generate_order_id()
        gross_amount = int(gross_amount)

        payload = self._build_charge_payload(
            payment_type=payment_type,
            order_id=order_id,
            gross_amount=gross_amount,
            customer_details=customer_details,
            item_details=item_details,
            payment_options=payment_options,
            custom_expiry=custom_expiry,
            notification_url=notification_url,
            metadata=metadata,
            custom_fields=custom_fields,
        )

        response = self.client.charge(payload)

        payment = self._create_payment_record(
            order_id=order_id,
            payment_type=payment_type,
            gross_amount=gross_amount,
            customer_details=customer_details,
            response=response,
            metadata=metadata,
            custom_fields=custom_fields,
            user=user,
        )

        if item_details:
            self._create_item_records(payment, item_details)

        return payment, response

    def _generate_order_id(self):
        return f"ORDER-{timezone.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8].upper()}"

    def _build_charge_payload(
        self,
        payment_type,
        order_id,
        gross_amount,
        customer_details=None,
        item_details=None,
        payment_options=None,
        custom_expiry=None,
        notification_url=None,
        metadata=None,
        custom_fields=None,
    ):
        payload = {
            "payment_type": payment_type,
            "transaction_details": {
                "order_id": order_id,
                "gross_amount": gross_amount,
            },
        }

        # Payment type specific options
        payment_options = payment_options or {}
        if payment_type == PaymentType.CREDIT_CARD:
            cc_opts = {"authentication": True}
            cc_opts.update(payment_options)
            payload["credit_card"] = cc_opts
        elif payment_type == PaymentType.GOPAY:
            gopay_opts = {}
            callback_url = payment_options.get("callback_url") or midtrans_settings.CALLBACK_URL_GOPAY
            if callback_url:
                gopay_opts["enable_callback"] = True
                gopay_opts["callback_url"] = callback_url
            gopay_opts.update({k: v for k, v in payment_options.items() if k != "callback_url"})
            if gopay_opts:
                payload["gopay"] = gopay_opts
        elif payment_type == PaymentType.SHOPEEPAY:
            sp_opts = {}
            callback_url = payment_options.get("callback_url") or midtrans_settings.CALLBACK_URL_SHOPEEPAY
            if callback_url:
                sp_opts["callback_url"] = callback_url
            sp_opts.update({k: v for k, v in payment_options.items() if k != "callback_url"})
            if sp_opts:
                payload["shopeepay"] = sp_opts
        elif payment_type == PaymentType.QRIS:
            qris_opts = {"acquirer": "gopay"}
            qris_opts.update(payment_options)
            payload["qris"] = qris_opts
        elif payment_type == PaymentType.BANK_TRANSFER:
            bank = payment_options.get("bank", "bca")
            payload["bank_transfer"] = {"bank": bank}
            if va_number := payment_options.get("va_number"):
                payload["bank_transfer"]["va_number"] = va_number
        elif payment_type == PaymentType.ECHANNEL:
            echannel_opts = {
                "bill_info1": payment_options.get("bill_info1", "Payment:"),
                "bill_info2": payment_options.get("bill_info2", "Online purchase"),
            }
            payload["echannel"] = echannel_opts
        elif payment_type == PaymentType.CSTORE:
            store = payment_options.get("store", "indomaret")
            payload["cstore"] = {"store": store}
        elif payment_type == PaymentType.OVO:
            # OVO requires customer phone
            pass

        # Customer details
        if customer_details:
            payload["customer_details"] = customer_details

        # Item details
        if item_details:
            payload["item_details"] = item_details

        # Custom expiry
        if custom_expiry:
            payload["custom_expiry"] = custom_expiry
        elif midtrans_settings.PAYMENT_EXPIRY_MINUTES:
            payload["custom_expiry"] = {
                "order_time": timezone.now().strftime("%Y-%m-%d %H:%M:%S %z"),
                "expiry_duration": midtrans_settings.PAYMENT_EXPIRY_MINUTES,
                "unit": midtrans_settings.CUSTOM_EXPIRY_UNIT,
            }

        # Notification URL override
        notification_url = notification_url or midtrans_settings.NOTIFICATION_URL
        if notification_url:
            payload["notification_url"] = notification_url

        # Metadata
        if metadata:
            payload["metadata"] = metadata

        # Custom fields
        if custom_fields:
            for i, value in enumerate(custom_fields[:3], 1):
                payload[f"custom_field{i}"] = value

        return payload

    @transaction.atomic
    def _create_payment_record(
        self, order_id, payment_type, gross_amount, customer_details, response, metadata, custom_fields, user
    ):
        customer_details = customer_details or {}
        custom_fields = custom_fields or []

        payment = MidtransPayment(
            order_id=order_id,
            transaction_id=response.get("transaction_id", ""),
            payment_type=payment_type,
            gross_amount=Decimal(str(gross_amount)),
            currency=response.get("currency", "IDR"),
            transaction_status=response.get("transaction_status", TransactionStatus.PENDING),
            fraud_status=response.get("fraud_status", ""),
            status_code=response.get("status_code", ""),
            status_message=response.get("status_message", ""),
            customer_first_name=customer_details.get("first_name", ""),
            customer_last_name=customer_details.get("last_name", ""),
            customer_email=customer_details.get("email", ""),
            customer_phone=customer_details.get("phone", ""),
            user=user,
            charge_response=response,
            metadata=metadata or {},
            custom_field1=custom_fields[0] if len(custom_fields) > 0 else "",
            custom_field2=custom_fields[1] if len(custom_fields) > 1 else "",
            custom_field3=custom_fields[2] if len(custom_fields) > 2 else "",
        )

        # Parse payment method specific info from response
        self._parse_payment_response(payment, response)

        # Parse timestamps (Midtrans returns naive datetimes in WIB/+07:00)
        if transaction_time := response.get("transaction_time"):
            dt = parse_datetime(transaction_time.replace(" ", "T"))
            if dt and timezone.is_naive(dt):
                dt = timezone.make_aware(dt)
            payment.transaction_time = dt

        if expiry_time := response.get("expiry_time"):
            dt = parse_datetime(expiry_time.replace(" ", "T"))
            if dt and timezone.is_naive(dt):
                dt = timezone.make_aware(dt)
            payment.expiry_time = dt

        # Bank for bank transfer
        if payment_type == PaymentType.BANK_TRANSFER:
            va_numbers = response.get("va_numbers", [])
            if va_numbers:
                payment.bank = va_numbers[0].get("bank", "")
                payment.va_number = va_numbers[0].get("va_number", "")
            permata = response.get("permata_va_number", "")
            if permata:
                payment.bank = "permata"
                payment.va_number = permata

        payment.save()
        return payment

    def _parse_payment_response(self, payment, response):
        # VA number
        va_numbers = response.get("va_numbers", [])
        if va_numbers:
            payment.va_number = va_numbers[0].get("va_number", "")

        # Permata VA
        if permata_va := response.get("permata_va_number"):
            payment.va_number = permata_va

        # Mandiri bill
        payment.bill_key = response.get("bill_key", "")
        payment.biller_code = response.get("biller_code", "")

        # CStore payment code
        payment.payment_code = response.get("payment_code", "")

        # Actions (redirect/deeplink/QR)
        actions = response.get("actions", [])
        for action in actions:
            action_name = action.get("name", "")
            action_url = action.get("url", "")
            if action_name in ("generate-qr-code", "generate-qr"):
                payment.qr_string = action_url
            elif action_name in ("deeplink-redirect",):
                payment.deeplink_url = action_url
            elif action_name in ("get-redirect-url",):
                payment.redirect_url = action_url

        # QR string direct — only use raw data if no image URL was found in actions
        if not payment.qr_string:
            if qr_string := response.get("qr_string"):
                payment.qr_string = qr_string

        # Top-level redirect_url (credit card 3DS returns this outside 'actions')
        if not payment.redirect_url:
            if redirect_url := response.get("redirect_url"):
                payment.redirect_url = redirect_url

    def _create_item_records(self, payment, item_details):
        items = []
        for item_data in item_details:
            items.append(
                MidtransPaymentItem(
                    payment=payment,
                    item_id=item_data.get("id", ""),
                    name=item_data.get("name", ""),
                    price=Decimal(str(item_data.get("price", 0))),
                    quantity=item_data.get("quantity", 1),
                    brand=item_data.get("brand", ""),
                    category=item_data.get("category", ""),
                    merchant_name=item_data.get("merchant_name", ""),
                    url=item_data.get("url", ""),
                )
            )
        MidtransPaymentItem.objects.bulk_create(items)

    # ─── Transaction Management ─────────────────────────────

    def get_status(self, payment):
        order_id = payment.order_id if isinstance(payment, MidtransPayment) else payment
        response = self.client.get_status(order_id)
        if isinstance(payment, MidtransPayment):
            self._update_payment_from_status(payment, response)
        return response

    def cancel_payment(self, payment):
        if isinstance(payment, str):
            payment = MidtransPayment.objects.get(order_id=payment)
        response = self.client.cancel(payment.order_id)
        self._update_payment_from_status(payment, response)
        return payment, response

    def expire_payment(self, payment):
        if isinstance(payment, str):
            payment = MidtransPayment.objects.get(order_id=payment)
        response = self.client.expire(payment.order_id)
        self._update_payment_from_status(payment, response)
        return payment, response

    def capture_payment(self, payment, amount=None):
        if isinstance(payment, str):
            payment = MidtransPayment.objects.get(order_id=payment)
        amount = amount or int(payment.gross_amount)
        response = self.client.capture(payment.transaction_id, amount)
        self._update_payment_from_status(payment, response)
        return payment, response

    @transaction.atomic
    def refund_payment(self, payment, amount, reason="", direct=False):
        if isinstance(payment, str):
            payment = MidtransPayment.objects.get(order_id=payment)

        refund_key = f"refund-{payment.order_id}-{uuid.uuid4().hex[:8]}"
        amount_int = int(amount)

        if direct:
            response = self.client.direct_refund(payment.order_id, refund_key, amount_int, reason)
        else:
            response = self.client.refund(payment.order_id, refund_key, amount_int, reason)

        refund = MidtransRefund.objects.create(
            payment=payment,
            refund_key=refund_key,
            amount=Decimal(str(amount)),
            reason=reason,
            is_direct=direct,
            status=response.get("transaction_status", "pending"),
            status_code=response.get("status_code", ""),
            status_message=response.get("status_message", ""),
            response=response,
        )

        payment.refund_amount += Decimal(str(amount))
        payment.refund_key = refund_key
        self._update_payment_from_status(payment, response)

        return payment, refund, response

    def approve_payment(self, payment):
        if isinstance(payment, str):
            payment = MidtransPayment.objects.get(order_id=payment)
        response = self.client.approve(payment.order_id)
        self._update_payment_from_status(payment, response)
        return payment, response

    def deny_payment(self, payment):
        if isinstance(payment, str):
            payment = MidtransPayment.objects.get(order_id=payment)
        response = self.client.deny(payment.order_id)
        self._update_payment_from_status(payment, response)
        return payment, response

    def _update_payment_from_status(self, payment, response):
        payment.transaction_status = response.get("transaction_status", payment.transaction_status)
        payment.fraud_status = response.get("fraud_status", payment.fraud_status)
        payment.status_code = response.get("status_code", payment.status_code)
        payment.status_message = response.get("status_message", payment.status_message)

        if settlement_time := response.get("settlement_time"):
            payment.settlement_time = parse_datetime(settlement_time.replace(" ", "T"))

        payment.save(update_fields=[
            "transaction_status", "fraud_status", "status_code",
            "status_message", "settlement_time", "updated_at",
        ])


class InvoiceService:
    """Service for managing Midtrans invoices."""

    def __init__(self, client: MidtransClient = None):
        self.client = client or get_client()

    @transaction.atomic
    def create_invoice(
        self,
        customer_name,
        customer_email,
        due_date,
        items,
        customer_phone="",
        customer_id="",
        notes="",
        order_id=None,
        invoice_number=None,
        user=None,
        metadata=None,
    ):
        from django_midtrans.models import MidtransInvoice, MidtransInvoiceItem

        order_id = order_id or f"INV-{timezone.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8].upper()}"
        invoice_number = invoice_number or self._generate_invoice_number()

        total_amount = sum(Decimal(str(item["price"])) * item.get("quantity", 1) for item in items)

        # Build Midtrans payload
        payload = {
            "order_id": order_id,
            "invoice_number": invoice_number,
            "due_date": due_date.strftime("%Y-%m-%d") if hasattr(due_date, "strftime") else str(due_date),
            "customer_details": {
                "name": customer_name,
                "email": customer_email,
                "phone": customer_phone,
            },
            "item_details": [
                {
                    "item_id": item.get("item_id", f"item-{i}"),
                    "description": item.get("description", item.get("name", "")),
                    "quantity": item.get("quantity", 1),
                    "price": int(item["price"]),
                }
                for i, item in enumerate(items, 1)
            ],
            "notes": notes,
            "payment_type": "payment_link",
        }

        if customer_id:
            payload["customer_details"]["id"] = customer_id

        response = self.client.create_invoice(payload)

        invoice = MidtransInvoice.objects.create(
            invoice_number=invoice_number,
            order_id=order_id,
            midtrans_invoice_id=response.get("id", ""),
            status="sent",
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            customer_id=customer_id,
            user=user,
            total_amount=total_amount,
            due_date=due_date,
            notes=notes,
            create_response=response,
            metadata=metadata or {},
        )

        invoice_items = []
        for i, item in enumerate(items, 1):
            invoice_items.append(
                MidtransInvoiceItem(
                    invoice=invoice,
                    item_id=item.get("item_id", f"item-{i}"),
                    description=item.get("description", item.get("name", "")),
                    quantity=item.get("quantity", 1),
                    price=Decimal(str(item["price"])),
                )
            )
        MidtransInvoiceItem.objects.bulk_create(invoice_items)

        return invoice, response

    def get_invoice_status(self, invoice):
        from django_midtrans.models import MidtransInvoice

        if isinstance(invoice, str):
            invoice = MidtransInvoice.objects.get(midtrans_invoice_id=invoice)
        response = self.client.get_invoice(invoice.midtrans_invoice_id)
        return response

    @transaction.atomic
    def void_invoice(self, invoice, reason=""):
        from django_midtrans.models import MidtransInvoice

        if isinstance(invoice, str):
            invoice = MidtransInvoice.objects.get(pk=invoice)
        response = self.client.void_invoice(invoice.midtrans_invoice_id, reason)
        invoice.status = "void"
        invoice.void_reason = reason
        invoice.save(update_fields=["status", "void_reason", "updated_at"])
        return invoice, response

    def _generate_invoice_number(self):
        prefix = midtrans_settings.INVOICE_PREFIX
        timestamp = timezone.now().strftime("%Y%m%d")
        unique = uuid.uuid4().hex[:6].upper()
        return f"{prefix}-{timestamp}-{unique}"


class SubscriptionService:
    """Service for managing Midtrans subscriptions."""

    def __init__(self, client: MidtransClient = None):
        self.client = client or get_client()

    @transaction.atomic
    def create_subscription(
        self,
        name,
        amount,
        payment_type,
        token="",
        interval=1,
        interval_unit="month",
        max_interval=12,
        start_time=None,
        retry_interval=1,
        retry_interval_unit="day",
        retry_max_interval=3,
        customer_details=None,
        gopay_account_id="",
        user=None,
        metadata=None,
    ):
        from django_midtrans.models import MidtransSubscription

        payload = {
            "name": name,
            "amount": str(int(amount)),
            "currency": midtrans_settings.DEFAULT_CURRENCY,
            "payment_type": payment_type,
            "schedule": {
                "interval": interval,
                "interval_unit": interval_unit,
                "max_interval": max_interval,
            },
            "retry_schedule": {
                "interval": retry_interval,
                "interval_unit": retry_interval_unit,
                "max_interval": retry_max_interval,
            },
        }

        if start_time:
            payload["schedule"]["start_time"] = start_time.strftime("%Y-%m-%d %H:%M:%S %z")

        if payment_type == PaymentType.CREDIT_CARD and token:
            payload["token"] = token
        elif payment_type == PaymentType.GOPAY and gopay_account_id:
            payload["gopay"] = {"account_id": gopay_account_id}

        if customer_details:
            payload["customer_details"] = customer_details

        response = self.client.create_subscription(payload)

        customer_details = customer_details or {}
        subscription = MidtransSubscription.objects.create(
            midtrans_subscription_id=response.get("id", ""),
            name=name,
            payment_type=payment_type,
            amount=Decimal(str(amount)),
            token=token or gopay_account_id,
            interval=interval,
            interval_unit=interval_unit,
            max_interval=max_interval,
            start_time=start_time,
            retry_interval=retry_interval,
            retry_interval_unit=retry_interval_unit,
            retry_max_interval=retry_max_interval,
            status=response.get("status", "active"),
            customer_first_name=customer_details.get("first_name", ""),
            customer_last_name=customer_details.get("last_name", ""),
            customer_email=customer_details.get("email", ""),
            customer_phone=customer_details.get("phone", ""),
            user=user,
            create_response=response,
            metadata=metadata or {},
        )

        return subscription, response

    def get_subscription_status(self, subscription):
        from django_midtrans.models import MidtransSubscription

        if isinstance(subscription, str):
            subscription = MidtransSubscription.objects.get(midtrans_subscription_id=subscription)
        return self.client.get_subscription(subscription.midtrans_subscription_id)

    @transaction.atomic
    def disable_subscription(self, subscription):
        from django_midtrans.models import MidtransSubscription

        if isinstance(subscription, str):
            subscription = MidtransSubscription.objects.get(pk=subscription)
        response = self.client.disable_subscription(subscription.midtrans_subscription_id)
        subscription.status = "disabled"
        subscription.save(update_fields=["status", "updated_at"])
        return subscription, response

    @transaction.atomic
    def enable_subscription(self, subscription):
        from django_midtrans.models import MidtransSubscription

        if isinstance(subscription, str):
            subscription = MidtransSubscription.objects.get(pk=subscription)
        response = self.client.enable_subscription(subscription.midtrans_subscription_id)
        subscription.status = "active"
        subscription.save(update_fields=["status", "updated_at"])
        return subscription, response

    @transaction.atomic
    def cancel_subscription(self, subscription):
        from django_midtrans.models import MidtransSubscription

        if isinstance(subscription, str):
            subscription = MidtransSubscription.objects.get(pk=subscription)
        response = self.client.cancel_subscription(subscription.midtrans_subscription_id)
        subscription.status = "cancelled"
        subscription.save(update_fields=["status", "updated_at"])
        return subscription, response

    @transaction.atomic
    def update_subscription(self, subscription, **kwargs):
        from django_midtrans.models import MidtransSubscription

        if isinstance(subscription, str):
            subscription = MidtransSubscription.objects.get(pk=subscription)

        payload = {}
        if "name" in kwargs:
            payload["name"] = kwargs["name"]
        if "amount" in kwargs:
            payload["amount"] = str(int(kwargs["amount"]))
        if "schedule" in kwargs:
            payload["schedule"] = kwargs["schedule"]

        response = self.client.update_subscription(subscription.midtrans_subscription_id, payload)

        if "name" in kwargs:
            subscription.name = kwargs["name"]
        if "amount" in kwargs:
            subscription.amount = Decimal(str(kwargs["amount"]))
        subscription.save()

        return subscription, response
