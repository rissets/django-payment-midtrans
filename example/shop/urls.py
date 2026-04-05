from django.urls import path

from shop.views import (
    AddToCartView,
    CartView,
    CheckoutView,
    CheckPaymentStatusAPI,
    HomeView,
    OrderDetailView,
    OrderListView,
    PaymentFinishView,
    PaymentStatusView,
    RemoveFromCartView,
    UpdateCartView,
)

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("cart/", CartView.as_view(), name="cart"),
    path("cart/add/<int:product_id>/", AddToCartView.as_view(), name="add-to-cart"),
    path("cart/update/", UpdateCartView.as_view(), name="update-cart"),
    path("cart/remove/<int:product_id>/", RemoveFromCartView.as_view(), name="remove-from-cart"),
    path("checkout/", CheckoutView.as_view(), name="checkout"),
    path("payment/<uuid:pk>/status/", PaymentStatusView.as_view(), name="payment-status"),
    path("payment/finish/", PaymentFinishView.as_view(), name="payment-finish"),
    path("orders/", OrderListView.as_view(), name="orders"),
    path("orders/<uuid:pk>/", OrderDetailView.as_view(), name="order-detail"),
    path("api/payment/<uuid:pk>/check/", CheckPaymentStatusAPI.as_view(), name="check-payment"),
]
