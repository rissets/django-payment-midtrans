"""
Interactive example views demonstrating all django_midtrans features.
"""

import json
import logging
from decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView

from django_midtrans.app_settings import midtrans_settings
from django_midtrans.exceptions import MidtransError
from django_midtrans.models import MidtransPayment
from django_midtrans.services import PaymentService

from shop.models import Order, OrderItem, Product

logger = logging.getLogger("shop")


# ─── Cart helpers ───────────────────────────────────────


def _get_cart(request):
    return request.session.get("cart", {})


def _save_cart(request, cart):
    request.session["cart"] = cart
    request.session.modified = True


def _cart_items(request):
    cart = _get_cart(request)
    if not cart:
        return [], Decimal("0")
    products = Product.objects.filter(pk__in=cart.keys(), is_active=True)
    items = []
    total = Decimal("0")
    for p in products:
        qty = cart.get(str(p.pk), 0)
        subtotal = p.price * qty
        items.append({"product": p, "quantity": qty, "subtotal": subtotal})
        total += subtotal
    return items, total


# ─── Product Views ──────────────────────────────────────


class HomeView(ListView):
    model = Product
    template_name = "shop/home.html"
    context_object_name = "products"

    def get_queryset(self):
        return Product.objects.filter(is_active=True)


# ─── Cart Views ─────────────────────────────────────────


class AddToCartView(View):
    def post(self, request, product_id):
        get_object_or_404(Product, pk=product_id, is_active=True)
        cart = _get_cart(request)
        key = str(product_id)
        cart[key] = cart.get(key, 0) + 1
        _save_cart(request, cart)
        return redirect("cart")


class UpdateCartView(View):
    def post(self, request):
        cart = _get_cart(request)
        try:
            data = json.loads(request.body)
            product_id = str(data.get("product_id"))
            quantity = int(data.get("quantity", 0))
            if quantity > 0:
                cart[product_id] = quantity
            else:
                cart.pop(product_id, None)
            _save_cart(request, cart)
            return JsonResponse({"success": True, "cart_count": sum(cart.values())})
        except (json.JSONDecodeError, ValueError):
            pass
        # Fallback: form submission
        for key, value in request.POST.items():
            if key.startswith("qty_"):
                pid = key[4:]
                qty = max(0, int(value))
                if qty > 0:
                    cart[pid] = qty
                else:
                    cart.pop(pid, None)
        _save_cart(request, cart)
        return redirect("cart")


class RemoveFromCartView(View):
    def post(self, request, product_id):
        cart = _get_cart(request)
        cart.pop(str(product_id), None)
        _save_cart(request, cart)
        return redirect("cart")


class CartView(TemplateView):
    template_name = "shop/cart.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        items, total = _cart_items(self.request)
        ctx["cart_items"] = items
        ctx["cart_total"] = total
        return ctx


# ─── Checkout ───────────────────────────────────────────


class CheckoutView(LoginRequiredMixin, View):
    login_url = "/admin/login/"

    def get(self, request):
        items, total = _cart_items(request)
        if not items:
            return redirect("cart")
        context = {
            "cart_items": items,
            "cart_total": total,
            "client_key": midtrans_settings.CLIENT_KEY,
            "is_production": midtrans_settings.IS_PRODUCTION,
        }
        return render(request, "shop/checkout.html", context)

    def post(self, request):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        items, total = _cart_items(request)
        if not items:
            return JsonResponse({"error": "Cart is empty"}, status=400)

        payment_type = data.get("payment_type", "bank_transfer")

        # Create order
        with transaction.atomic():
            order = Order.objects.create(user=request.user, total=total)
            item_details = []
            for item in items:
                p = item["product"]
                qty = item["quantity"]
                OrderItem.objects.create(order=order, product=p, quantity=qty, price=p.price)
                item_details.append({
                    "id": str(p.pk),
                    "name": p.name[:50],
                    "price": int(p.price),
                    "quantity": qty,
                })

        # Build payment options
        payment_options = {}
        finish_url = request.build_absolute_uri(f"/payment/finish/?order_id={order.id}")

        if payment_type == "bank_transfer":
            payment_options["bank"] = data.get("bank", "bca")
        elif payment_type == "echannel":
            payment_options["bill_info1"] = "Payment:"
            payment_options["bill_info2"] = f"Order {str(order.id)[:8]}"
        elif payment_type == "qris":
            payment_options["acquirer"] = "gopay"
        elif payment_type == "credit_card":
            payment_options["token_id"] = data.get("token_id", "")
            payment_options["authentication"] = True
        elif payment_type == "gopay":
            payment_options["callback_url"] = finish_url
        elif payment_type == "shopeepay":
            payment_options["callback_url"] = finish_url
        elif payment_type == "cstore":
            payment_options["store"] = data.get("store", "indomaret")

        customer = {
            "first_name": data.get("first_name") or request.user.first_name or request.user.username,
            "last_name": data.get("last_name") or request.user.last_name or "",
            "email": data.get("email") or request.user.email or f"{request.user.username}@example.com",
            "phone": data.get("phone") or "08123456789",
        }

        service = PaymentService()
        try:
            payment, response = service.create_charge(
                payment_type=payment_type,
                gross_amount=total,
                customer_details=customer,
                item_details=item_details,
                payment_options=payment_options,
                user=request.user,
            )

            order.midtrans_payment = payment
            order.save(update_fields=["midtrans_payment"])

            # Clear cart
            _save_cart(request, {})

            result = {
                "success": True,
                "order_id": str(order.id),
                "payment_order_id": payment.order_id,
                "transaction_status": payment.transaction_status,
                "payment_type": payment.payment_type,
                "status_url": f"/payment/{order.id}/status/",
            }

            if payment.redirect_url:
                result["redirect_url"] = payment.redirect_url
            if payment.deeplink_url:
                result["deeplink_url"] = payment.deeplink_url

            return JsonResponse(result, status=201)

        except MidtransError as e:
            logger.error("Charge failed: %s", str(e))
            order.status = Order.Status.CANCELLED
            order.save(update_fields=["status"])
            return JsonResponse(
                {"error": str(e), "detail": getattr(e, "data", {})},
                status=getattr(e, "status_code", 400) or 400,
            )


# ─── Payment Status & Finish ───────────────────────────


class PaymentStatusView(LoginRequiredMixin, DetailView):
    login_url = "/admin/login/"
    model = Order
    template_name = "shop/payment_status.html"
    context_object_name = "order"

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).select_related("midtrans_payment")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        payment = self.object.midtrans_payment
        if payment:
            # Sync order status in case payment was settled via API/webhook
            _sync_order_status(self.object, payment)
            ctx["payment"] = payment
            ctx["is_production"] = midtrans_settings.IS_PRODUCTION
            ctx["client_key"] = midtrans_settings.CLIENT_KEY
        return ctx


class PaymentFinishView(LoginRequiredMixin, TemplateView):
    login_url = "/admin/login/"
    template_name = "shop/payment_finish.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        order_id = self.request.GET.get("order_id")
        if order_id:
            try:
                order = Order.objects.select_related("midtrans_payment").get(
                    id=order_id, user=self.request.user,
                )
                ctx["order"] = order
                ctx["payment"] = order.midtrans_payment
            except (Order.DoesNotExist, ValueError):
                pass
        return ctx


# ─── Orders ─────────────────────────────────────────────


class OrderListView(LoginRequiredMixin, ListView):
    login_url = "/admin/login/"
    model = Order
    template_name = "shop/orders.html"
    context_object_name = "orders"
    paginate_by = 20

    def get_queryset(self):
        qs = (
            Order.objects.filter(user=self.request.user)
            .select_related("midtrans_payment")
            .prefetch_related("items__product")
        )
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)
        return qs


class OrderDetailView(LoginRequiredMixin, DetailView):
    login_url = "/admin/login/"
    model = Order
    template_name = "shop/order_detail.html"
    context_object_name = "order"

    def get_queryset(self):
        return (
            Order.objects.filter(user=self.request.user)
            .select_related("midtrans_payment")
            .prefetch_related("items__product")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        payment = self.object.midtrans_payment
        if payment:
            _sync_order_status(self.object, payment)
        return ctx


# ─── AJAX API ───────────────────────────────────────────


class CheckPaymentStatusAPI(View):
    def get(self, request, pk):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Not authenticated"}, status=401)

        order = get_object_or_404(Order, pk=pk, user=request.user)
        payment = order.midtrans_payment
        if not payment:
            return JsonResponse({"error": "No payment"}, status=404)

        if payment.is_pending:
            service = PaymentService()
            try:
                service.get_status(payment)
                payment.refresh_from_db()
            except MidtransError:
                pass

        # Sync order status based on payment status
        _sync_order_status(order, payment)

        return JsonResponse({
            "transaction_status": payment.transaction_status,
            "payment_type": payment.payment_type,
            "is_paid": payment.is_paid,
            "is_pending": payment.is_pending,
            "is_failed": payment.is_failed,
            "order_status": order.status,
        })


def _sync_order_status(order, payment):
    """Sync Order.status with the MidtransPayment.transaction_status."""
    if not payment:
        return
    if payment.is_paid and order.status == Order.Status.PENDING:
        order.status = Order.Status.PAID
        order.save(update_fields=["status", "updated_at"])
        # Also create invoice if not already created
        from shop.signals import _create_invoice_for_order
        _create_invoice_for_order(order, payment)
    elif payment.is_failed and order.status == Order.Status.PENDING:
        order.status = Order.Status.CANCELLED
        order.save(update_fields=["status", "updated_at"])
    elif payment.is_refunded and order.status != Order.Status.REFUNDED:
        order.status = Order.Status.REFUNDED
        order.save(update_fields=["status", "updated_at"])
