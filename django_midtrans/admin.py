import logging
from decimal import Decimal

from django.contrib import admin
from django.db.models import Count, Sum, Q
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from django_midtrans.constants import (
    FraudStatus,
    InvoiceStatus,
    NotificationStatus,
    PaymentType,
    SubscriptionStatus,
    TransactionStatus,
)
from django_midtrans.exceptions import MidtransError
from django_midtrans.models import (
    MidtransInvoice,
    MidtransInvoiceItem,
    MidtransNotification,
    MidtransPayment,
    MidtransPaymentItem,
    MidtransRefund,
    MidtransSubscription,
)
from django_midtrans.services import InvoiceService, PaymentService, SubscriptionService

logger = logging.getLogger("django_midtrans")

# Try to import unfold, fall back to default admin
try:
    from unfold.admin import ModelAdmin, TabularInline, StackedInline
    from unfold.contrib.filters.admin import (
        ChoicesDropdownFilter,
        RangeDateFilter,
        RangeNumericFilter,
    )
    from unfold.decorators import action, display
    from unfold.enums import ActionVariant

    HAS_UNFOLD = True
except ImportError:
    from django.contrib.admin import ModelAdmin, TabularInline, StackedInline

    HAS_UNFOLD = False

    # Fallback decorators
    def action(**kwargs):
        def decorator(func):
            description = kwargs.get("description", "")
            func.short_description = description
            return func
        return decorator

    def display(**kwargs):
        def decorator(func):
            func.short_description = kwargs.get("description", "")
            func.admin_order_field = kwargs.get("ordering")
            return func
        return decorator


# ─── Inlines ────────────────────────────────────────────

class PaymentItemInline(TabularInline):
    model = MidtransPaymentItem
    extra = 0
    readonly_fields = ["item_id", "name", "price", "quantity", "brand", "category", "subtotal"]
    fields = ["item_id", "name", "price", "quantity", "brand", "category", "subtotal"]

    def subtotal(self, obj):
        return obj.subtotal
    subtotal.short_description = _("Subtotal")

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class RefundInline(TabularInline):
    model = MidtransRefund
    extra = 0
    readonly_fields = ["refund_key", "amount", "reason", "is_direct", "status", "status_code", "created_at"]
    fields = ["refund_key", "amount", "reason", "is_direct", "status", "status_code", "created_at"]

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class NotificationInline(TabularInline):
    model = MidtransNotification
    extra = 0
    readonly_fields = [
        "transaction_status", "fraud_status", "payment_type",
        "status_code", "status", "created_at",
    ]
    fields = [
        "transaction_status", "fraud_status", "payment_type",
        "status_code", "status", "created_at",
    ]
    ordering = ["-created_at"]

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class InvoiceItemInline(TabularInline):
    model = MidtransInvoiceItem
    extra = 1
    fields = ["item_id", "description", "quantity", "price"]


# ─── Payment Admin ──────────────────────────────────────

@admin.register(MidtransPayment)
class MidtransPaymentAdmin(ModelAdmin):
    list_display = [
        "order_id",
        "display_payment_type",
        "display_amount",
        "display_status",
        "display_fraud_status",
        "customer_email",
        "display_created_at",
    ]
    list_display_links = ["order_id"]
    search_fields = ["order_id", "transaction_id", "customer_email", "customer_first_name", "customer_last_name"]
    readonly_fields = [
        "id", "order_id", "transaction_id", "payment_type", "bank",
        "gross_amount", "currency", "transaction_status", "fraud_status",
        "status_code", "status_message",
        "customer_first_name", "customer_last_name", "customer_email", "customer_phone",
        "va_number", "bill_key", "biller_code", "payment_code",
        "redirect_url", "deeplink_url", "qr_string",
        "transaction_time", "settlement_time", "expiry_time",
        "refund_amount", "refund_key",
        "charge_response", "metadata",
        "custom_field1", "custom_field2", "custom_field3",
        "created_at", "updated_at",
    ]
    inlines = [PaymentItemInline, RefundInline, NotificationInline]
    list_per_page = 25

    if HAS_UNFOLD:
        list_filter_submit = True
        list_filter = [
            ("payment_type", ChoicesDropdownFilter),
            ("transaction_status", ChoicesDropdownFilter),
            ("fraud_status", ChoicesDropdownFilter),
            ("created_at", RangeDateFilter),
            ("gross_amount", RangeNumericFilter),
        ]
        actions_detail = ["action_check_status", "action_cancel_payment", "action_expire_payment"]
    else:
        list_filter = ["payment_type", "transaction_status", "fraud_status", "created_at"]

    fieldsets = (
        (_("Transaction Info"), {
            "fields": (
                "id", "order_id", "transaction_id",
                "payment_type", "bank", "gross_amount", "currency",
            ),
        }),
        (_("Status"), {
            "fields": (
                "transaction_status", "fraud_status",
                "status_code", "status_message",
            ),
        }),
        (_("Customer"), {
            "fields": (
                "customer_first_name", "customer_last_name",
                "customer_email", "customer_phone", "user",
            ),
        }),
        (_("Payment Details"), {
            "fields": (
                "va_number", "bill_key", "biller_code", "payment_code",
                "redirect_url", "deeplink_url", "qr_string",
            ),
            "classes": ("collapse",),
        }),
        (_("Timestamps"), {
            "fields": (
                "transaction_time", "settlement_time", "expiry_time",
                "created_at", "updated_at",
            ),
        }),
        (_("Refund"), {
            "fields": ("refund_amount", "refund_key"),
            "classes": ("collapse",),
        }),
        (_("Raw Data"), {
            "fields": ("charge_response", "metadata", "custom_field1", "custom_field2", "custom_field3"),
            "classes": ("collapse",),
        }),
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    if HAS_UNFOLD:
        @display(
            description=_("Payment Type"),
            ordering="payment_type",
            label={
                PaymentType.CREDIT_CARD: "info",
                PaymentType.GOPAY: "success",
                PaymentType.SHOPEEPAY: "warning",
                PaymentType.QRIS: "info",
                PaymentType.BANK_TRANSFER: "primary",
                PaymentType.ECHANNEL: "primary",
                PaymentType.OVO: "success",
            },
        )
        def display_payment_type(self, obj):
            return obj.payment_type

        @display(
            description=_("Status"),
            ordering="transaction_status",
            label={
                TransactionStatus.PENDING: "warning",
                TransactionStatus.CAPTURE: "success",
                TransactionStatus.SETTLEMENT: "success",
                TransactionStatus.DENY: "danger",
                TransactionStatus.CANCEL: "danger",
                TransactionStatus.EXPIRE: "danger",
                TransactionStatus.REFUND: "info",
                TransactionStatus.PARTIAL_REFUND: "info",
                TransactionStatus.AUTHORIZE: "warning",
            },
        )
        def display_status(self, obj):
            return obj.transaction_status

        @display(
            description=_("Fraud"),
            ordering="fraud_status",
            label={
                FraudStatus.ACCEPT: "success",
                FraudStatus.CHALLENGE: "warning",
                FraudStatus.DENY: "danger",
            },
        )
        def display_fraud_status(self, obj):
            return obj.fraud_status or "-"

        @display(description=_("Amount"), ordering="gross_amount")
        def display_amount(self, obj):
            return f"Rp {obj.gross_amount:,.0f}"

        @display(description=_("Created"), ordering="created_at")
        def display_created_at(self, obj):
            return obj.created_at.strftime("%d %b %Y %H:%M")

        @action(description=_("Check Status"), icon="sync", variant=ActionVariant.INFO)
        def action_check_status(self, request, object_id):
            payment = MidtransPayment.objects.get(pk=object_id)
            service = PaymentService()
            try:
                service.get_status(payment)
            except MidtransError as e:
                logger.error("Status check failed for %s: %s", payment.order_id, str(e))
            return redirect(reverse("admin:django_midtrans_midtranspayment_change", args=[object_id]))

        @action(description=_("Cancel Payment"), icon="cancel", variant=ActionVariant.DANGER)
        def action_cancel_payment(self, request, object_id):
            payment = MidtransPayment.objects.get(pk=object_id)
            if not payment.is_final:
                service = PaymentService()
                try:
                    service.cancel_payment(payment)
                except MidtransError as e:
                    logger.error("Cancel failed for %s: %s", payment.order_id, str(e))
            return redirect(reverse("admin:django_midtrans_midtranspayment_change", args=[object_id]))

        @action(description=_("Expire Payment"), icon="timer_off", variant=ActionVariant.WARNING)
        def action_expire_payment(self, request, object_id):
            payment = MidtransPayment.objects.get(pk=object_id)
            if payment.is_pending:
                service = PaymentService()
                try:
                    service.expire_payment(payment)
                except MidtransError as e:
                    logger.error("Expire failed for %s: %s", payment.order_id, str(e))
            return redirect(reverse("admin:django_midtrans_midtranspayment_change", args=[object_id]))
    else:
        def display_payment_type(self, obj):
            return obj.get_payment_type_display()
        display_payment_type.short_description = _("Payment Type")
        display_payment_type.admin_order_field = "payment_type"

        def display_status(self, obj):
            return obj.get_transaction_status_display()
        display_status.short_description = _("Status")
        display_status.admin_order_field = "transaction_status"

        def display_fraud_status(self, obj):
            return obj.get_fraud_status_display() if obj.fraud_status else "-"
        display_fraud_status.short_description = _("Fraud")

        def display_amount(self, obj):
            return f"Rp {obj.gross_amount:,.0f}"
        display_amount.short_description = _("Amount")
        display_amount.admin_order_field = "gross_amount"

        def display_created_at(self, obj):
            return obj.created_at.strftime("%d %b %Y %H:%M")
        display_created_at.short_description = _("Created")
        display_created_at.admin_order_field = "created_at"


# ─── Notification Admin ─────────────────────────────────

@admin.register(MidtransNotification)
class MidtransNotificationAdmin(ModelAdmin):
    list_display = [
        "order_id",
        "display_transaction_status",
        "display_processing_status",
        "payment_type",
        "created_at",
    ]
    list_display_links = ["order_id"]
    search_fields = ["order_id", "transaction_id"]
    readonly_fields = [
        "id", "payment", "order_id", "transaction_id",
        "transaction_status", "fraud_status", "payment_type",
        "status_code", "gross_amount", "signature_key",
        "status", "raw_payload", "error_message",
        "created_at", "updated_at",
    ]
    list_per_page = 50

    if HAS_UNFOLD:
        list_filter_submit = True
        list_filter = [
            ("transaction_status", ChoicesDropdownFilter),
            ("status", ChoicesDropdownFilter),
            ("created_at", RangeDateFilter),
        ]

        @display(
            description=_("Txn Status"),
            ordering="transaction_status",
            label={
                TransactionStatus.SETTLEMENT: "success",
                TransactionStatus.CAPTURE: "success",
                TransactionStatus.PENDING: "warning",
                TransactionStatus.DENY: "danger",
                TransactionStatus.CANCEL: "danger",
                TransactionStatus.EXPIRE: "danger",
                TransactionStatus.REFUND: "info",
            },
        )
        def display_transaction_status(self, obj):
            return obj.transaction_status

        @display(
            description=_("Processing"),
            ordering="status",
            label={
                NotificationStatus.PROCESSED: "success",
                NotificationStatus.RECEIVED: "warning",
                NotificationStatus.FAILED: "danger",
                NotificationStatus.DUPLICATE: "info",
                NotificationStatus.INVALID_SIGNATURE: "danger",
            },
        )
        def display_processing_status(self, obj):
            return obj.status
    else:
        list_filter = ["transaction_status", "status", "created_at"]

        def display_transaction_status(self, obj):
            return obj.get_transaction_status_display()
        display_transaction_status.short_description = _("Txn Status")

        def display_processing_status(self, obj):
            return obj.get_status_display()
        display_processing_status.short_description = _("Processing")

    fieldsets = (
        (_("Notification Info"), {
            "fields": (
                "id", "payment", "order_id", "transaction_id",
                "transaction_status", "fraud_status", "payment_type",
                "status_code", "gross_amount",
            ),
        }),
        (_("Verification"), {
            "fields": ("signature_key", "status", "error_message"),
        }),
        (_("Raw Data"), {
            "fields": ("raw_payload",),
            "classes": ("collapse",),
        }),
        (_("Timestamps"), {
            "fields": ("created_at", "updated_at"),
        }),
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


# ─── Invoice Admin ──────────────────────────────────────

@admin.register(MidtransInvoice)
class MidtransInvoiceAdmin(ModelAdmin):
    list_display = [
        "invoice_number",
        "customer_name",
        "display_total",
        "display_invoice_status",
        "due_date",
        "created_at",
    ]
    list_display_links = ["invoice_number"]
    search_fields = ["invoice_number", "order_id", "customer_name", "customer_email"]
    inlines = [InvoiceItemInline]
    list_per_page = 25

    if HAS_UNFOLD:
        list_filter_submit = True
        list_filter = [
            ("status", ChoicesDropdownFilter),
            ("due_date", RangeDateFilter),
            ("created_at", RangeDateFilter),
        ]
        actions_detail = ["action_void_invoice"]

        @display(
            description=_("Status"),
            ordering="status",
            label={
                InvoiceStatus.DRAFT: "info",
                InvoiceStatus.SENT: "warning",
                InvoiceStatus.PAID: "success",
                InvoiceStatus.OVERDUE: "danger",
                InvoiceStatus.VOID: "danger",
                InvoiceStatus.PARTIAL: "warning",
            },
        )
        def display_invoice_status(self, obj):
            return obj.status

        @display(description=_("Total"), ordering="total_amount")
        def display_total(self, obj):
            return f"Rp {obj.total_amount:,.0f}"

        @action(description=_("Void Invoice"), icon="block", variant=ActionVariant.DANGER)
        def action_void_invoice(self, request, object_id):
            invoice = MidtransInvoice.objects.get(pk=object_id)
            if invoice.status not in [InvoiceStatus.VOID, InvoiceStatus.PAID]:
                service = InvoiceService()
                try:
                    service.void_invoice(invoice, reason="Voided from admin")
                except MidtransError as e:
                    logger.error("Void failed for %s: %s", invoice.invoice_number, str(e))
            return redirect(reverse("admin:django_midtrans_midtransinvoice_change", args=[object_id]))
    else:
        list_filter = ["status", "due_date", "created_at"]

        def display_invoice_status(self, obj):
            return obj.get_status_display()
        display_invoice_status.short_description = _("Status")

        def display_total(self, obj):
            return f"Rp {obj.total_amount:,.0f}"
        display_total.short_description = _("Total")

    fieldsets = (
        (_("Invoice Info"), {
            "fields": (
                "invoice_number", "order_id", "midtrans_invoice_id", "status",
            ),
        }),
        (_("Customer"), {
            "fields": (
                "customer_name", "customer_email", "customer_phone",
                "customer_id", "user",
            ),
        }),
        (_("Amount & Dates"), {
            "fields": (
                "total_amount", "currency", "due_date", "paid_at",
            ),
        }),
        (_("Notes"), {
            "fields": ("notes", "void_reason"),
        }),
        (_("Related"), {
            "fields": ("payment",),
            "classes": ("collapse",),
        }),
        (_("Raw Data"), {
            "fields": ("create_response", "metadata"),
            "classes": ("collapse",),
        }),
    )


# ─── Subscription Admin ────────────────────────────────

@admin.register(MidtransSubscription)
class MidtransSubscriptionAdmin(ModelAdmin):
    list_display = [
        "name",
        "display_subscription_status",
        "payment_type",
        "display_amount",
        "display_schedule",
        "created_at",
    ]
    list_display_links = ["name"]
    search_fields = ["name", "midtrans_subscription_id", "customer_email"]
    list_per_page = 25

    if HAS_UNFOLD:
        list_filter_submit = True
        list_filter = [
            ("status", ChoicesDropdownFilter),
            ("payment_type", ChoicesDropdownFilter),
            ("created_at", RangeDateFilter),
        ]
        actions_detail = [
            "action_disable_subscription",
            "action_enable_subscription",
            "action_cancel_subscription",
        ]

        @display(
            description=_("Status"),
            ordering="status",
            label={
                SubscriptionStatus.ACTIVE: "success",
                SubscriptionStatus.INACTIVE: "warning",
                SubscriptionStatus.DISABLED: "info",
                SubscriptionStatus.CANCELLED: "danger",
            },
        )
        def display_subscription_status(self, obj):
            return obj.status

        @display(description=_("Amount"), ordering="amount")
        def display_amount(self, obj):
            return f"Rp {obj.amount:,.0f}"

        @display(description=_("Schedule"))
        def display_schedule(self, obj):
            return obj.schedule_display

        @action(description=_("Disable"), icon="pause_circle", variant=ActionVariant.WARNING)
        def action_disable_subscription(self, request, object_id):
            sub = MidtransSubscription.objects.get(pk=object_id)
            if sub.status == SubscriptionStatus.ACTIVE:
                service = SubscriptionService()
                try:
                    service.disable_subscription(sub)
                except MidtransError as e:
                    logger.error("Disable failed for %s: %s", sub.midtrans_subscription_id, str(e))
            return redirect(reverse("admin:django_midtrans_midtranssubscription_change", args=[object_id]))

        @action(description=_("Enable"), icon="play_circle", variant=ActionVariant.SUCCESS)
        def action_enable_subscription(self, request, object_id):
            sub = MidtransSubscription.objects.get(pk=object_id)
            if sub.status == SubscriptionStatus.DISABLED:
                service = SubscriptionService()
                try:
                    service.enable_subscription(sub)
                except MidtransError as e:
                    logger.error("Enable failed for %s: %s", sub.midtrans_subscription_id, str(e))
            return redirect(reverse("admin:django_midtrans_midtranssubscription_change", args=[object_id]))

        @action(description=_("Cancel"), icon="cancel", variant=ActionVariant.DANGER)
        def action_cancel_subscription(self, request, object_id):
            sub = MidtransSubscription.objects.get(pk=object_id)
            if sub.status not in [SubscriptionStatus.CANCELLED]:
                service = SubscriptionService()
                try:
                    service.cancel_subscription(sub)
                except MidtransError as e:
                    logger.error("Cancel failed for %s: %s", sub.midtrans_subscription_id, str(e))
            return redirect(reverse("admin:django_midtrans_midtranssubscription_change", args=[object_id]))
    else:
        list_filter = ["status", "payment_type", "created_at"]

        def display_subscription_status(self, obj):
            return obj.get_status_display()
        display_subscription_status.short_description = _("Status")

        def display_amount(self, obj):
            return f"Rp {obj.amount:,.0f}"
        display_amount.short_description = _("Amount")

        def display_schedule(self, obj):
            return obj.schedule_display
        display_schedule.short_description = _("Schedule")

    fieldsets = (
        (_("Subscription Info"), {
            "fields": (
                "midtrans_subscription_id", "name", "status",
                "payment_type", "amount", "currency", "token",
            ),
        }),
        (_("Schedule"), {
            "fields": (
                "interval", "interval_unit", "max_interval",
                "start_time", "current_interval",
            ),
        }),
        (_("Retry Schedule"), {
            "fields": (
                "retry_interval", "retry_interval_unit", "retry_max_interval",
            ),
        }),
        (_("Customer"), {
            "fields": (
                "customer_first_name", "customer_last_name",
                "customer_email", "customer_phone", "user",
            ),
        }),
        (_("Raw Data"), {
            "fields": ("create_response", "metadata"),
            "classes": ("collapse",),
        }),
    )


# ─── Refund Admin ───────────────────────────────────────

@admin.register(MidtransRefund)
class MidtransRefundAdmin(ModelAdmin):
    list_display = ["refund_key", "display_payment", "display_refund_amount", "status", "is_direct", "created_at"]
    list_display_links = ["refund_key"]
    search_fields = ["refund_key", "payment__order_id"]
    readonly_fields = [
        "id", "payment", "refund_key", "amount", "reason",
        "is_direct", "status", "status_code", "status_message",
        "response", "created_at", "updated_at",
    ]
    list_per_page = 25

    if HAS_UNFOLD:
        list_filter_submit = True
        list_filter = [
            ("created_at", RangeDateFilter),
        ]

        @display(description=_("Payment"), ordering="payment__order_id")
        def display_payment(self, obj):
            return obj.payment.order_id

        @display(description=_("Amount"), ordering="amount")
        def display_refund_amount(self, obj):
            return f"Rp {obj.amount:,.0f}"
    else:
        list_filter = ["status", "is_direct", "created_at"]

        def display_payment(self, obj):
            return obj.payment.order_id
        display_payment.short_description = _("Payment")

        def display_refund_amount(self, obj):
            return f"Rp {obj.amount:,.0f}"
        display_refund_amount.short_description = _("Amount")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
