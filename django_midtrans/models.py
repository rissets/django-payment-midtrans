import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from django_midtrans.constants import (
    BankType,
    FraudStatus,
    InvoiceStatus,
    NotificationStatus,
    PaymentType,
    SubscriptionStatus,
    TransactionStatus,
)


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(_("created at"), auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        abstract = True


class MidtransPayment(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_id = models.CharField(
        _("order ID"),
        max_length=50,
        unique=True,
        db_index=True,
        help_text=_("Unique order ID sent to Midtrans (max 50 chars)"),
    )
    transaction_id = models.CharField(
        _("transaction ID"),
        max_length=100,
        blank=True,
        default="",
        db_index=True,
        help_text=_("Midtrans-generated transaction UUID"),
    )

    # Payment info
    payment_type = models.CharField(
        _("payment type"),
        max_length=30,
        choices=PaymentType.CHOICES,
        db_index=True,
    )
    bank = models.CharField(
        _("bank"),
        max_length=20,
        choices=BankType.CHOICES,
        blank=True,
        default="",
        help_text=_("Bank for VA payments"),
    )
    gross_amount = models.DecimalField(
        _("gross amount"),
        max_digits=15,
        decimal_places=2,
    )
    currency = models.CharField(_("currency"), max_length=5, default="IDR")

    # Status
    transaction_status = models.CharField(
        _("transaction status"),
        max_length=30,
        choices=TransactionStatus.CHOICES,
        default=TransactionStatus.PENDING,
        db_index=True,
    )
    fraud_status = models.CharField(
        _("fraud status"),
        max_length=20,
        choices=FraudStatus.CHOICES,
        blank=True,
        default="",
    )
    status_code = models.CharField(_("status code"), max_length=10, blank=True, default="")
    status_message = models.CharField(_("status message"), max_length=255, blank=True, default="")

    # Customer details
    customer_first_name = models.CharField(_("first name"), max_length=255, blank=True, default="")
    customer_last_name = models.CharField(_("last name"), max_length=255, blank=True, default="")
    customer_email = models.EmailField(_("email"), blank=True, default="")
    customer_phone = models.CharField(_("phone"), max_length=50, blank=True, default="")

    # Optional FK to user
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="midtrans_payments",
        verbose_name=_("user"),
    )

    # Payment method specific
    va_number = models.CharField(_("VA number"), max_length=50, blank=True, default="")
    bill_key = models.CharField(_("bill key"), max_length=50, blank=True, default="")
    biller_code = models.CharField(_("biller code"), max_length=20, blank=True, default="")
    payment_code = models.CharField(_("payment code"), max_length=50, blank=True, default="")
    redirect_url = models.URLField(_("redirect URL"), blank=True, default="")
    deeplink_url = models.URLField(_("deeplink URL"), max_length=500, blank=True, default="")
    qr_string = models.TextField(_("QR string"), blank=True, default="")

    # Timestamps from Midtrans
    transaction_time = models.DateTimeField(_("transaction time"), null=True, blank=True)
    settlement_time = models.DateTimeField(_("settlement time"), null=True, blank=True)
    expiry_time = models.DateTimeField(_("expiry time"), null=True, blank=True)

    # Refund
    refund_amount = models.DecimalField(
        _("refund amount"),
        max_digits=15,
        decimal_places=2,
        default=0,
    )
    refund_key = models.CharField(_("refund key"), max_length=100, blank=True, default="")

    # Raw response & metadata
    charge_response = models.JSONField(_("charge response"), default=dict, blank=True)
    metadata = models.JSONField(_("metadata"), default=dict, blank=True)
    custom_field1 = models.CharField(_("custom field 1"), max_length=255, blank=True, default="")
    custom_field2 = models.CharField(_("custom field 2"), max_length=255, blank=True, default="")
    custom_field3 = models.CharField(_("custom field 3"), max_length=255, blank=True, default="")

    class Meta:
        verbose_name = _("Midtrans Payment")
        verbose_name_plural = _("Midtrans Payments")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["transaction_status", "payment_type"]),
            models.Index(fields=["customer_email"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.order_id} - {self.get_payment_type_display()} ({self.transaction_status})"

    @property
    def is_paid(self):
        return self.transaction_status in TransactionStatus.SUCCESS_STATUSES

    @property
    def is_pending(self):
        return self.transaction_status == TransactionStatus.PENDING

    @property
    def is_failed(self):
        return self.transaction_status in TransactionStatus.FAILED_STATUSES

    @property
    def is_final(self):
        return self.transaction_status in TransactionStatus.FINAL_STATUSES

    @property
    def is_refunded(self):
        return self.transaction_status in [TransactionStatus.REFUND, TransactionStatus.PARTIAL_REFUND]

    @property
    def net_amount(self):
        return self.gross_amount - self.refund_amount

    @property
    def is_expired(self):
        if self.expiry_time and self.is_pending:
            expiry = self.expiry_time
            if timezone.is_naive(expiry):
                expiry = timezone.make_aware(expiry)
            return timezone.now() > expiry
        return self.transaction_status == TransactionStatus.EXPIRE


class MidtransPaymentItem(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.ForeignKey(
        MidtransPayment,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name=_("payment"),
    )
    item_id = models.CharField(_("item ID"), max_length=50, blank=True, default="")
    name = models.CharField(_("name"), max_length=50)
    price = models.DecimalField(_("price"), max_digits=15, decimal_places=2)
    quantity = models.PositiveIntegerField(_("quantity"), default=1)
    brand = models.CharField(_("brand"), max_length=50, blank=True, default="")
    category = models.CharField(_("category"), max_length=50, blank=True, default="")
    merchant_name = models.CharField(_("merchant name"), max_length=50, blank=True, default="")
    url = models.URLField(_("URL"), blank=True, default="")

    class Meta:
        verbose_name = _("Payment Item")
        verbose_name_plural = _("Payment Items")

    def __str__(self):
        return f"{self.name} x{self.quantity}"

    @property
    def subtotal(self):
        return self.price * self.quantity


class MidtransNotification(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.ForeignKey(
        MidtransPayment,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name=_("payment"),
        null=True,
        blank=True,
    )
    order_id = models.CharField(_("order ID"), max_length=50, db_index=True)
    transaction_id = models.CharField(_("transaction ID"), max_length=100, blank=True, default="")
    transaction_status = models.CharField(
        _("transaction status"),
        max_length=30,
        choices=TransactionStatus.CHOICES,
    )
    fraud_status = models.CharField(
        _("fraud status"),
        max_length=20,
        choices=FraudStatus.CHOICES,
        blank=True,
        default="",
    )
    payment_type = models.CharField(
        _("payment type"),
        max_length=30,
        choices=PaymentType.CHOICES,
        blank=True,
        default="",
    )
    status_code = models.CharField(_("status code"), max_length=10, blank=True, default="")
    gross_amount = models.CharField(_("gross amount"), max_length=20, blank=True, default="")
    signature_key = models.CharField(_("signature key"), max_length=256, blank=True, default="")
    status = models.CharField(
        _("processing status"),
        max_length=30,
        choices=NotificationStatus.CHOICES,
        default=NotificationStatus.RECEIVED,
        db_index=True,
    )
    raw_payload = models.JSONField(_("raw payload"), default=dict)
    error_message = models.TextField(_("error message"), blank=True, default="")

    class Meta:
        verbose_name = _("Midtrans Notification")
        verbose_name_plural = _("Midtrans Notifications")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["order_id", "transaction_status"]),
        ]

    def __str__(self):
        return f"Notification {self.order_id} - {self.transaction_status} ({self.status})"


class MidtransInvoice(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice_number = models.CharField(
        _("invoice number"),
        max_length=50,
        unique=True,
        db_index=True,
    )
    order_id = models.CharField(_("order ID"), max_length=50, unique=True)
    midtrans_invoice_id = models.CharField(
        _("Midtrans invoice ID"),
        max_length=100,
        blank=True,
        default="",
    )

    # Status
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=InvoiceStatus.CHOICES,
        default=InvoiceStatus.DRAFT,
        db_index=True,
    )

    # Customer
    customer_name = models.CharField(_("customer name"), max_length=255)
    customer_email = models.EmailField(_("customer email"))
    customer_phone = models.CharField(_("customer phone"), max_length=50, blank=True, default="")
    customer_id = models.CharField(_("customer ID"), max_length=50, blank=True, default="")

    # Optional FK to user
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="midtrans_invoices",
        verbose_name=_("user"),
    )

    # Amounts
    total_amount = models.DecimalField(_("total amount"), max_digits=15, decimal_places=2, default=0)
    currency = models.CharField(_("currency"), max_length=5, default="IDR")

    # Dates
    due_date = models.DateField(_("due date"))
    paid_at = models.DateTimeField(_("paid at"), null=True, blank=True)

    # Details
    notes = models.TextField(_("notes"), blank=True, default="")
    void_reason = models.CharField(_("void reason"), max_length=255, blank=True, default="")

    # Related payment
    payment = models.OneToOneField(
        MidtransPayment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invoice",
        verbose_name=_("payment"),
    )

    # Raw response
    create_response = models.JSONField(_("create response"), default=dict, blank=True)
    metadata = models.JSONField(_("metadata"), default=dict, blank=True)

    class Meta:
        verbose_name = _("Midtrans Invoice")
        verbose_name_plural = _("Midtrans Invoices")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "due_date"]),
            models.Index(fields=["customer_email"]),
        ]

    def __str__(self):
        return f"{self.invoice_number} - {self.customer_name} ({self.status})"

    @property
    def is_overdue(self):
        if self.status in [InvoiceStatus.DRAFT, InvoiceStatus.SENT]:
            return timezone.now().date() > self.due_date
        return False


class MidtransInvoiceItem(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(
        MidtransInvoice,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name=_("invoice"),
    )
    item_id = models.CharField(_("item ID"), max_length=50, blank=True, default="")
    description = models.CharField(_("description"), max_length=255)
    quantity = models.PositiveIntegerField(_("quantity"), default=1)
    price = models.DecimalField(_("price"), max_digits=15, decimal_places=2)

    class Meta:
        verbose_name = _("Invoice Item")
        verbose_name_plural = _("Invoice Items")

    def __str__(self):
        return f"{self.description} x{self.quantity}"

    @property
    def subtotal(self):
        return self.price * self.quantity


class MidtransSubscription(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    midtrans_subscription_id = models.CharField(
        _("Midtrans subscription ID"),
        max_length=100,
        unique=True,
        db_index=True,
    )
    name = models.CharField(_("name"), max_length=255)

    # Payment
    payment_type = models.CharField(
        _("payment type"),
        max_length=30,
        choices=[
            (PaymentType.CREDIT_CARD, _("Credit Card")),
            (PaymentType.GOPAY, _("GoPay")),
        ],
    )
    amount = models.DecimalField(_("amount"), max_digits=15, decimal_places=2)
    currency = models.CharField(_("currency"), max_length=5, default="IDR")

    # Token
    token = models.CharField(
        _("token"),
        max_length=255,
        blank=True,
        default="",
        help_text=_("Card token or GoPay account ID"),
    )

    # Schedule
    interval = models.PositiveIntegerField(_("interval"), default=1)
    interval_unit = models.CharField(
        _("interval unit"),
        max_length=10,
        choices=[("day", _("Day")), ("week", _("Week")), ("month", _("Month"))],
        default="month",
    )
    max_interval = models.PositiveIntegerField(_("max interval"), default=12)
    start_time = models.DateTimeField(_("start time"), null=True, blank=True)
    current_interval = models.PositiveIntegerField(_("current interval"), default=0)

    # Retry
    retry_interval = models.PositiveIntegerField(_("retry interval"), default=1)
    retry_interval_unit = models.CharField(_("retry interval unit"), max_length=10, default="day")
    retry_max_interval = models.PositiveIntegerField(_("retry max interval"), default=3)

    # Status
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=SubscriptionStatus.CHOICES,
        default=SubscriptionStatus.ACTIVE,
        db_index=True,
    )

    # Customer
    customer_first_name = models.CharField(_("first name"), max_length=255, blank=True, default="")
    customer_last_name = models.CharField(_("last name"), max_length=255, blank=True, default="")
    customer_email = models.EmailField(_("email"), blank=True, default="")
    customer_phone = models.CharField(_("phone"), max_length=50, blank=True, default="")

    # Optional FK to user
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="midtrans_subscriptions",
        verbose_name=_("user"),
    )

    # Raw response
    create_response = models.JSONField(_("create response"), default=dict, blank=True)
    metadata = models.JSONField(_("metadata"), default=dict, blank=True)

    class Meta:
        verbose_name = _("Midtrans Subscription")
        verbose_name_plural = _("Midtrans Subscriptions")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"

    @property
    def schedule_display(self):
        return f"Every {self.interval} {self.interval_unit}(s)"


class MidtransRefund(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.ForeignKey(
        MidtransPayment,
        on_delete=models.CASCADE,
        related_name="refunds",
        verbose_name=_("payment"),
    )
    refund_key = models.CharField(_("refund key"), max_length=100, unique=True)
    amount = models.DecimalField(_("amount"), max_digits=15, decimal_places=2)
    reason = models.CharField(_("reason"), max_length=255, blank=True, default="")
    is_direct = models.BooleanField(_("direct refund"), default=False)

    # Status
    status = models.CharField(_("status"), max_length=30, default="pending")
    status_code = models.CharField(_("status code"), max_length=10, blank=True, default="")
    status_message = models.CharField(_("status message"), max_length=255, blank=True, default="")

    # Raw response
    response = models.JSONField(_("response"), default=dict, blank=True)

    class Meta:
        verbose_name = _("Midtrans Refund")
        verbose_name_plural = _("Midtrans Refunds")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Refund {self.refund_key} - {self.amount}"
