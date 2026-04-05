# Quick Start

Get a payment running in 5 minutes.

## 1. Add to INSTALLED_APPS

```python
# settings.py
INSTALLED_APPS = [
    # Optional: Unfold admin (must be BEFORE django.contrib.admin)
    "unfold",
    "unfold.contrib.filters",

    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Required third-party
    "rest_framework",
    "django_celery_beat",       # Optional: only if using Celery Beat

    # The package
    "django_midtrans",
]
```

## 2. Configure Midtrans Settings

```python
# settings.py
import os

MIDTRANS = {
    "SERVER_KEY": os.environ.get("MIDTRANS_SERVER_KEY", ""),
    "CLIENT_KEY": os.environ.get("MIDTRANS_CLIENT_KEY", ""),
    "MERCHANT_ID": os.environ.get("MIDTRANS_MERCHANT_ID", ""),
    "IS_PRODUCTION": False,
    "NOTIFICATION_URL": os.environ.get("MIDTRANS_NOTIFICATION_URL", ""),
}
```

## 3. Add URL Routes

```python
# urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/midtrans/", include("django_midtrans.urls")),
]
```

## 4. Run Migrations

```bash
python manage.py migrate django_midtrans
```

This creates 7 database tables:

- `midtrans_payment` — Payment records
- `midtrans_paymentitem` — Line items for each payment
- `midtrans_notification` — Webhook notification audit log
- `midtrans_invoice` — Invoice records
- `midtrans_invoiceitem` — Invoice line items
- `midtrans_subscription` — Recurring payment subscriptions
- `midtrans_refund` — Refund records

## 5. Create Your First Payment

```python
from django_midtrans.services import PaymentService

service = PaymentService()

# Create a Bank Transfer (BCA Virtual Account) payment
payment = service.create_charge(
    payment_type="bank_transfer",
    gross_amount=150000,
    order_id="ORDER-001",
    bank="bca",
    customer_details={
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        "phone": "081234567890",
    },
    item_details=[
        {
            "id": "ITEM-1",
            "name": "T-Shirt",
            "price": 150000,
            "quantity": 1,
        },
    ],
)

# The payment is now created in Midtrans and stored in your database
print(payment.order_id)          # "ORDER-001"
print(payment.va_number)         # "1234567890123456"
print(payment.transaction_status)  # "pending"
print(payment.is_pending)        # True
print(payment.expiry_time)       # datetime when VA expires
```

## 6. Handle Webhook Notifications

When the customer pays, Midtrans will send a webhook notification to your `NOTIFICATION_URL`. The package handles this automatically:

```python
# your_app/signals.py
from django.dispatch import receiver
from django_midtrans.signals import payment_settled

@receiver(payment_settled)
def handle_payment_success(sender, notification, payload, **kwargs):
    order_id = payload.get("order_id")
    # Update your order status, send email, etc.
    print(f"Payment settled for order {order_id}!")
```

Make sure to import this in your app's `apps.py`:

```python
# your_app/apps.py
from django.apps import AppConfig

class YourAppConfig(AppConfig):
    name = "your_app"

    def ready(self):
        import your_app.signals  # noqa
```

## Next Steps

- {doc}`configuration` — Full configuration reference
- {doc}`payments` — All payment methods with examples
- {doc}`webhooks` — Webhook setup and handling
- {doc}`signals` — All available lifecycle signals
- {doc}`celery` — Async tasks and periodic scheduling
