# Models

The `django_midtrans.models` module defines all database models for storing payment, invoice, subscription, and notification data.

All models inherit from `TimeStampedModel` which provides `created_at` and `updated_at` fields.

---

## TimeStampedModel

Abstract base model providing timestamp fields.

| Field | Type | Description |
|-------|------|-------------|
| `created_at` | `DateTimeField` | Auto-set on creation, indexed. |
| `updated_at` | `DateTimeField` | Auto-set on every save. |

---

## MidtransPayment

The core payment model. Stores full transaction state from Midtrans.

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUIDField` | Primary key (auto-generated UUID4). |
| `order_id` | `CharField(50)` | Unique order ID sent to Midtrans. Indexed. |
| `transaction_id` | `CharField(100)` | Midtrans-generated transaction UUID. |
| `payment_type` | `CharField(30)` | Payment method (see `PaymentType` constants). Indexed. |
| `bank` | `CharField(20)` | Bank for VA payments (see `BankType` constants). |
| `gross_amount` | `DecimalField(15,2)` | Total charge amount. |
| `currency` | `CharField(5)` | Currency code (default: `"IDR"`). |
| `transaction_status` | `CharField(30)` | Current status (see `TransactionStatus`). Indexed. |
| `fraud_status` | `CharField(20)` | Fraud detection result (see `FraudStatus`). |
| `status_code` | `CharField(10)` | Midtrans HTTP status code. |
| `status_message` | `CharField(255)` | Midtrans status message. |
| `customer_first_name` | `CharField(255)` | Customer first name. |
| `customer_last_name` | `CharField(255)` | Customer last name. |
| `customer_email` | `EmailField` | Customer email. |
| `customer_phone` | `CharField(50)` | Customer phone number. |
| `user` | `ForeignKey(AUTH_USER_MODEL)` | Optional link to Django user. `SET_NULL` on delete. Related name: `midtrans_payments`. |
| `va_number` | `CharField(50)` | Virtual Account number (bank transfer). |
| `bill_key` | `CharField(50)` | Mandiri bill key (e-channel). |
| `biller_code` | `CharField(20)` | Mandiri biller code (e-channel). |
| `payment_code` | `CharField(50)` | Convenience store payment code. |
| `redirect_url` | `URLField` | 3DS redirect URL (credit card). |
| `deeplink_url` | `URLField(500)` | Mobile deeplink URL (GoPay, ShopeePay). |
| `qr_string` | `TextField` | QR code data string (QRIS). |
| `transaction_time` | `DateTimeField` | Transaction creation time from Midtrans. |
| `settlement_time` | `DateTimeField` | Settlement time from Midtrans. |
| `expiry_time` | `DateTimeField` | Payment expiry time. |
| `refund_amount` | `DecimalField(15,2)` | Total refunded amount (default: 0). |
| `refund_key` | `CharField(100)` | Latest refund key. |
| `charge_response` | `JSONField` | Full raw charge API response. |
| `metadata` | `JSONField` | Arbitrary metadata dict. |
| `custom_field1` | `CharField(255)` | Custom field 1. |
| `custom_field2` | `CharField(255)` | Custom field 2. |
| `custom_field3` | `CharField(255)` | Custom field 3. |
| `created_at` | `DateTimeField` | Record creation timestamp. |
| `updated_at` | `DateTimeField` | Last update timestamp. |

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `is_paid` | `bool` | `True` if status is `capture` or `settlement`. |
| `is_pending` | `bool` | `True` if status is `pending`. |
| `is_failed` | `bool` | `True` if status is `deny`, `cancel`, `expire`, or `failure`. |
| `is_final` | `bool` | `True` if status is a terminal state (no further changes expected). |
| `is_refunded` | `bool` | `True` if status is `refund` or `partial_refund`. |
| `net_amount` | `Decimal` | `gross_amount - refund_amount`. |
| `is_expired` | `bool` | `True` if past expiry time and still pending, or status is `expire`. |

### Database Indexes

- `(transaction_status, payment_type)`
- `(customer_email)`
- `(created_at)`

### Example

```python
from django_midtrans.models import MidtransPayment

# Get all paid payments
paid = MidtransPayment.objects.filter(
    transaction_status__in=["capture", "settlement"]
)

# Check a specific payment
payment = MidtransPayment.objects.get(order_id="ORDER-20240101-ABC12345")
print(payment.is_paid)       # True
print(payment.net_amount)    # Decimal('95000.00')
```

---

## MidtransPaymentItem

Line items for a payment.

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUIDField` | Primary key. |
| `payment` | `ForeignKey(MidtransPayment)` | Parent payment. Related name: `items`. |
| `item_id` | `CharField(50)` | External item ID. |
| `name` | `CharField(50)` | Item name. |
| `price` | `DecimalField(15,2)` | Unit price. |
| `quantity` | `PositiveIntegerField` | Quantity (default: 1). |
| `brand` | `CharField(50)` | Brand name. |
| `category` | `CharField(50)` | Category name. |
| `merchant_name` | `CharField(50)` | Merchant name. |
| `url` | `URLField` | Item URL. |

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `subtotal` | `Decimal` | `price × quantity` |

---

## MidtransNotification

Stores incoming webhook notifications from Midtrans.

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUIDField` | Primary key. |
| `payment` | `ForeignKey(MidtransPayment)` | Linked payment (nullable). Related name: `notifications`. |
| `order_id` | `CharField(50)` | Order ID from notification. Indexed. |
| `transaction_id` | `CharField(100)` | Transaction ID from notification. |
| `transaction_status` | `CharField(30)` | Status reported by Midtrans. |
| `fraud_status` | `CharField(20)` | Fraud status from notification. |
| `payment_type` | `CharField(30)` | Payment type from notification. |
| `status_code` | `CharField(10)` | HTTP status code. |
| `gross_amount` | `CharField(20)` | Gross amount string. |
| `signature_key` | `CharField(256)` | SHA-512 signature for verification. |
| `status` | `CharField(30)` | Processing status: `received`, `processed`, `failed`, `duplicate`, `invalid_signature`. |
| `raw_payload` | `JSONField` | Complete raw notification JSON. |
| `error_message` | `TextField` | Error details if processing failed. |

---

## MidtransInvoice

Invoice model for Midtrans invoice/payment link API.

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUIDField` | Primary key. |
| `invoice_number` | `CharField(50)` | Unique invoice number. |
| `order_id` | `CharField(50)` | Unique order ID. |
| `midtrans_invoice_id` | `CharField(100)` | Midtrans-generated invoice ID. |
| `status` | `CharField(20)` | `draft`, `sent`, `paid`, `overdue`, `void`, `partial`. |
| `customer_name` | `CharField(255)` | Customer name. |
| `customer_email` | `EmailField` | Customer email. |
| `customer_phone` | `CharField(50)` | Customer phone. |
| `customer_id` | `CharField(50)` | External customer ID. |
| `user` | `ForeignKey(AUTH_USER_MODEL)` | Optional Django user. Related name: `midtrans_invoices`. |
| `total_amount` | `DecimalField(15,2)` | Invoice total. |
| `currency` | `CharField(5)` | Default: `"IDR"`. |
| `due_date` | `DateField` | Due date. |
| `paid_at` | `DateTimeField` | Payment timestamp (nullable). |
| `notes` | `TextField` | Invoice notes. |
| `void_reason` | `CharField(255)` | Reason for voiding. |
| `payment` | `OneToOneField(MidtransPayment)` | Linked payment (nullable). Related name: `invoice`. |
| `create_response` | `JSONField` | Raw Midtrans create response. |
| `metadata` | `JSONField` | Arbitrary metadata. |

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `is_overdue` | `bool` | `True` if past due date and status is `draft` or `sent`. |

---

## MidtransInvoiceItem

Line items for an invoice.

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUIDField` | Primary key. |
| `invoice` | `ForeignKey(MidtransInvoice)` | Parent invoice. Related name: `items`. |
| `item_id` | `CharField(50)` | External item ID. |
| `description` | `CharField(255)` | Item description. |
| `quantity` | `PositiveIntegerField` | Quantity (default: 1). |
| `price` | `DecimalField(15,2)` | Unit price. |

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `subtotal` | `Decimal` | `price × quantity` |

---

## MidtransSubscription

Recurring subscription model.

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUIDField` | Primary key. |
| `midtrans_subscription_id` | `CharField(100)` | Midtrans subscription ID. Unique, indexed. |
| `name` | `CharField(255)` | Subscription name. |
| `payment_type` | `CharField(30)` | `credit_card` or `gopay`. |
| `amount` | `DecimalField(15,2)` | Recurring amount. |
| `currency` | `CharField(5)` | Default: `"IDR"`. |
| `token` | `CharField(255)` | Card token or GoPay account ID. |
| `interval` | `PositiveIntegerField` | Billing interval count (default: 1). |
| `interval_unit` | `CharField(10)` | `"day"`, `"week"`, or `"month"`. |
| `max_interval` | `PositiveIntegerField` | Max billing cycles (default: 12). |
| `start_time` | `DateTimeField` | Subscription start time (nullable). |
| `current_interval` | `PositiveIntegerField` | Current interval count. |
| `retry_interval` | `PositiveIntegerField` | Retry interval count. |
| `retry_interval_unit` | `CharField(10)` | Retry unit (default: `"day"`). |
| `retry_max_interval` | `PositiveIntegerField` | Max retries (default: 3). |
| `status` | `CharField(20)` | `active`, `inactive`, `disabled`, `cancelled`. |
| `customer_first_name` | `CharField(255)` | Customer first name. |
| `customer_last_name` | `CharField(255)` | Customer last name. |
| `customer_email` | `EmailField` | Customer email. |
| `customer_phone` | `CharField(50)` | Customer phone. |
| `user` | `ForeignKey(AUTH_USER_MODEL)` | Optional Django user. Related name: `midtrans_subscriptions`. |
| `create_response` | `JSONField` | Raw create response. |
| `metadata` | `JSONField` | Arbitrary metadata. |

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `schedule_display` | `str` | Human-readable schedule, e.g. `"Every 1 month(s)"`. |

---

## MidtransRefund

Refund record linked to a payment.

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUIDField` | Primary key. |
| `payment` | `ForeignKey(MidtransPayment)` | Parent payment. Related name: `refunds`. |
| `refund_key` | `CharField(100)` | Unique refund key. |
| `amount` | `DecimalField(15,2)` | Refund amount. |
| `reason` | `CharField(255)` | Refund reason. |
| `is_direct` | `BooleanField` | Whether this was a direct (online) refund. |
| `status` | `CharField(30)` | Refund status (default: `"pending"`). |
| `status_code` | `CharField(10)` | Midtrans status code. |
| `status_message` | `CharField(255)` | Midtrans status message. |
| `response` | `JSONField` | Raw refund API response. |

### Example

```python
from django_midtrans.models import MidtransPayment

payment = MidtransPayment.objects.get(order_id="ORDER-123")

# Access related objects
for item in payment.items.all():
    print(f"{item.name}: {item.subtotal}")

for notification in payment.notifications.all():
    print(f"{notification.transaction_status} at {notification.created_at}")

for refund in payment.refunds.all():
    print(f"Refund {refund.refund_key}: {refund.amount}")
```
