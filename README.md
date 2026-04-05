# Django Payment Midtrans

A comprehensive, plug-and-play Django package for **Midtrans Core API** payment gateway integration. Supports all payment methods (Credit Card, Bank Transfer/VA, E-Wallets, QRIS, etc.), invoicing, subscriptions, notifications, and integrates seamlessly with Django Admin (Unfold), Celery & Beat.

> **Note**: This package uses Midtrans **Core API** directly — NOT Snap.

## Features

- **Full Core API Integration**: Direct charge, cancel, expire, refund, capture
- **All Payment Methods**: Credit Card, GoPay, ShopeePay, QRIS, OVO, Bank Transfer (BCA/BNI/BRI/Permata/CIMB), Mandiri Bill, Convenience Store
- **Invoice Management**: Create, get, void invoices via Midtrans Invoicing API
- **Subscription/Recurring**: Create, manage, disable, enable, cancel subscriptions
- **Webhook Notifications**: Secure signature verification, idempotent processing
- **Django REST Framework API**: Complete REST endpoints for payments
- **Django Admin (Unfold)**: Beautiful admin interface with filters, actions, dashboard
- **Celery & Beat**: Async payment processing, scheduled status checks, expiry handling
- **Customizable & Scalable**: Override services, signals for custom logic, configurable settings

## Installation

```bash
pip install django-payment-midtrans
```

With Unfold admin support:
```bash
pip install django-payment-midtrans[unfold]
```

## Quick Setup

### 1. Add to INSTALLED_APPS

```python
INSTALLED_APPS = [
    "unfold",                    # Optional, before django.contrib.admin
    "unfold.contrib.filters",    # Optional
    "django.contrib.admin",
    # ...
    "rest_framework",
    "django_celery_beat",
    "django_midtrans",
]
```

### 2. Configure Settings

```python
MIDTRANS = {
    "SERVER_KEY": "SB-Mid-server-xxxx",
    "CLIENT_KEY": "SB-Mid-client-xxxx",
    "MERCHANT_ID": "G123456789",
    "IS_PRODUCTION": False,
    "NOTIFICATION_URL": "https://yourdomain.com/api/midtrans/notification/",
    "PAYMENT_EXPIRY_MINUTES": 1440,  # 24 hours default
    "AUTO_CHECK_STATUS_INTERVAL": 300,  # 5 minutes
    "ENABLED_PAYMENT_METHODS": [
        "credit_card", "gopay", "shopeepay", "qris",
        "bank_transfer", "echannel", "cstore",
    ],
}
```

### 3. Add URLs

```python
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/midtrans/", include("django_midtrans.urls")),
]
```

### 4. Run Migrations

```bash
python manage.py migrate django_midtrans
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/midtrans/charge/` | Create a new payment charge |
| GET | `/api/midtrans/payments/` | List all payments |
| GET | `/api/midtrans/payments/{id}/` | Get payment detail |
| POST | `/api/midtrans/payments/{id}/cancel/` | Cancel payment |
| POST | `/api/midtrans/payments/{id}/expire/` | Expire payment |
| POST | `/api/midtrans/payments/{id}/refund/` | Refund payment |
| GET | `/api/midtrans/payments/{id}/status/` | Check payment status |
| POST | `/api/midtrans/notification/` | Webhook notification handler |
| POST | `/api/midtrans/invoices/` | Create invoice |
| GET | `/api/midtrans/invoices/` | List invoices |
| GET | `/api/midtrans/invoices/{id}/` | Get invoice detail |
| POST | `/api/midtrans/invoices/{id}/void/` | Void invoice |
| POST | `/api/midtrans/subscriptions/` | Create subscription |
| GET | `/api/midtrans/subscriptions/` | List subscriptions |
| POST | `/api/midtrans/subscriptions/{id}/disable/` | Disable subscription |
| POST | `/api/midtrans/subscriptions/{id}/enable/` | Enable subscription |
| POST | `/api/midtrans/subscriptions/{id}/cancel/` | Cancel subscription |

## License

MIT
