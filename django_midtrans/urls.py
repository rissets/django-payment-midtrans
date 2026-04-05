from django.urls import include, path
from rest_framework.routers import DefaultRouter

from django_midtrans.views import (
    ChargeView,
    InvoiceDetailView,
    InvoiceListCreateView,
    InvoiceVoidView,
    NotificationView,
    PaymentViewSet,
    SubscriptionActionView,
    SubscriptionDetailView,
    SubscriptionListCreateView,
)

app_name = "django_midtrans"

router = DefaultRouter()
router.register(r"payments", PaymentViewSet, basename="payment")

urlpatterns = [
    # Charge
    path("charge/", ChargeView.as_view(), name="charge"),

    # Notification webhook (public)
    path("notification/", NotificationView.as_view(), name="notification"),

    # Invoices
    path("invoices/", InvoiceListCreateView.as_view(), name="invoice-list-create"),
    path("invoices/<uuid:pk>/", InvoiceDetailView.as_view(), name="invoice-detail"),
    path("invoices/<uuid:pk>/void/", InvoiceVoidView.as_view(), name="invoice-void"),

    # Subscriptions
    path("subscriptions/", SubscriptionListCreateView.as_view(), name="subscription-list-create"),
    path("subscriptions/<uuid:pk>/", SubscriptionDetailView.as_view(), name="subscription-detail"),
    path(
        "subscriptions/<uuid:pk>/<str:action_name>/",
        SubscriptionActionView.as_view(),
        name="subscription-action",
    ),

    # Payment ViewSet (list, detail, actions)
    path("", include(router.urls)),
]
