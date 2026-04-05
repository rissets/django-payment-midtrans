from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from shop.models import Order, OrderItem, Product

try:
    from unfold.admin import ModelAdmin, TabularInline
    from unfold.contrib.filters.admin import ChoicesDropdownFilter, RangeDateFilter
    from unfold.decorators import display

    HAS_UNFOLD = True
except ImportError:
    from django.contrib.admin import ModelAdmin, TabularInline

    HAS_UNFOLD = False

    def display(**kwargs):
        def decorator(func):
            func.short_description = kwargs.get("description", "")
            return func
        return decorator


class OrderItemInline(TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ["product", "quantity", "price", "display_subtotal"]
    fields = ["product", "quantity", "price", "display_subtotal"]

    def display_subtotal(self, obj):
        return f"Rp {obj.subtotal:,.0f}" if obj.pk else "-"
    display_subtotal.short_description = _("Subtotal")

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ["name", "display_price", "stock", "is_active", "created_at"]
    list_filter = [("is_active", ChoicesDropdownFilter)] if HAS_UNFOLD else ["is_active"]
    search_fields = ["name", "description"]
    list_editable = ["stock", "is_active"]
    list_per_page = 25

    if HAS_UNFOLD:
        @display(description=_("Price"), ordering="price")
        def display_price(self, obj):
            return f"Rp {obj.price:,.0f}"
    else:
        def display_price(self, obj):
            return f"Rp {obj.price:,.0f}"
        display_price.short_description = _("Price")
        display_price.admin_order_field = "price"


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = ["display_id", "user", "display_status", "display_total", "display_payment", "created_at"]
    list_display_links = ["display_id"]
    search_fields = ["id", "user__username", "user__email"]
    readonly_fields = ["id", "user", "total", "midtrans_payment", "created_at", "updated_at"]
    inlines = [OrderItemInline]
    list_per_page = 25

    if HAS_UNFOLD:
        list_filter_submit = True
        list_filter = [
            ("status", ChoicesDropdownFilter),
            ("created_at", RangeDateFilter),
        ]

        @display(description=_("Order"), ordering="id")
        def display_id(self, obj):
            return str(obj.id)[:13] + "..."

        @display(
            description=_("Status"),
            ordering="status",
            label={
                "pending": "warning",
                "paid": "success",
                "shipped": "info",
                "cancelled": "danger",
                "refunded": "info",
            },
        )
        def display_status(self, obj):
            return obj.status

        @display(description=_("Total"), ordering="total")
        def display_total(self, obj):
            return f"Rp {obj.total:,.0f}"

        @display(description=_("Payment"))
        def display_payment(self, obj):
            if obj.midtrans_payment:
                return obj.midtrans_payment.get_payment_type_display()
            return "-"
    else:
        list_filter = ["status", "created_at"]

        def display_id(self, obj):
            return str(obj.id)[:13] + "..."
        display_id.short_description = _("Order")

        def display_status(self, obj):
            return obj.get_status_display()
        display_status.short_description = _("Status")
        display_status.admin_order_field = "status"

        def display_total(self, obj):
            return f"Rp {obj.total:,.0f}"
        display_total.short_description = _("Total")
        display_total.admin_order_field = "total"

        def display_payment(self, obj):
            if obj.midtrans_payment:
                return obj.midtrans_payment.get_payment_type_display()
            return "-"
        display_payment.short_description = _("Payment")

    fieldsets = (
        (_("Order Info"), {
            "fields": ("id", "user", "status", "total"),
        }),
        (_("Payment"), {
            "fields": ("midtrans_payment",),
        }),
        (_("Notes"), {
            "fields": ("notes",),
        }),
        (_("Timestamps"), {
            "fields": ("created_at", "updated_at"),
        }),
    )
