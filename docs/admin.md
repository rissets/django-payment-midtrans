# Django Admin

`django_midtrans` registers all models in the Django admin with rich display, filtering, and actions.

## Registered Models

### Payments (`MidtransPaymentAdmin`)

**List View:**

| Column | Description |
|--------|-------------|
| Order ID | Unique order identifier |
| Payment Type | Colored label (e.g., `credit_card`, `gopay`) |
| Amount | Formatted with currency |
| Status | Colored badge (green=settled, yellow=pending, red=failed) |
| Fraud Status | Colored badge |
| Customer Email | Customer's email address |
| Created At | Timestamp |

**Filters:** payment_type, transaction_status, fraud_status, created_at (date range), gross_amount (range)

**Search:** order_id, transaction_id, customer_email, customer_first_name, customer_last_name

**Inlines:**
- Payment Items — line items associated with the payment
- Refunds — refund records for the payment
- Notifications — webhook notifications received

**Detail Actions (Unfold theme):**
- **Check Status** — Syncs the payment status from Midtrans API
- **Cancel Payment** — Cancels the payment (if not in a final state)
- **Expire Payment** — Forces payment expiry (if pending)

### Notifications (`MidtransNotificationAdmin`)

**List View:**

| Column | Description |
|--------|-------------|
| Order ID | Related order |
| Transaction Status | Colored label |
| Processing Status | Colored label (received/processed/failed/duplicate/invalid) |
| Payment Type | Method used |
| Created At | When notification arrived |

**Filters:** transaction_status, processing status, created_at

**Search:** order_id, transaction_id

**Read-only:** All fields (notifications cannot be edited)

### Invoices (`MidtransInvoiceAdmin`)

**List View:**

| Column | Description |
|--------|-------------|
| Invoice Number | Auto-generated number |
| Customer Name | Customer name |
| Total | Formatted amount |
| Status | Colored badge (draft/sent/paid/overdue/void) |
| Due Date | Payment deadline |
| Created At | Timestamp |

**Filters:** status, due_date (range), created_at (range)

**Search:** invoice_number, order_id, customer_name, customer_email

**Detail Actions (Unfold theme):**
- **Void Invoice** — Voids the invoice

**Inlines:**
- Invoice Items

### Subscriptions (`MidtransSubscriptionAdmin`)

**List View:**

| Column | Description |
|--------|-------------|
| Subscription ID | Midtrans subscription ID |
| Name | Subscription name |
| Status | Colored badge (active/inactive/disabled/cancelled) |
| Amount | Formatted amount |

**Filters:** status, created_at

## Unfold Theme Integration

The admin automatically detects if [django-unfold](https://github.com/unfoldadmin/django-unfold) is installed and provides enhanced UI:

- **Colored badges** for payment types, statuses, and fraud statuses
- **Detail view actions** (Check Status, Cancel, Expire, Void)
- **Dashboard widgets** from the example app
- **Custom filters** with range selectors

### Enable Unfold

```bash
pip install django-payment-midtrans[unfold]
```

```python
# settings.py
INSTALLED_APPS = [
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    # ... 
    "django.contrib.admin",
    "django_midtrans",
]
```

### Without Unfold

The admin works with the standard Django admin theme. Status fields display as plain text without colored badges, and detail actions are not available (use the API or management commands instead).

## Customizing the Admin

To extend or override the admin:

```python
# yourapp/admin.py
from django.contrib import admin
from django_midtrans.admin import MidtransPaymentAdmin
from django_midtrans.models import MidtransPayment

# Unregister the default
admin.site.unregister(MidtransPayment)

# Register your custom version
@admin.register(MidtransPayment)
class CustomPaymentAdmin(MidtransPaymentAdmin):
    list_display = MidtransPaymentAdmin.list_display + ("user",)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(user=request.user)
        return qs
```
