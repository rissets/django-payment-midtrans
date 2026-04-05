# Services

The `django_midtrans.services` module provides high-level service classes for interacting with Midtrans payments, invoices, and subscriptions.

---

## PaymentService

High-level service for creating and managing Midtrans payments. Override methods in subclasses for custom behavior.

### Constructor

```python
PaymentService(client=None)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `client` | `MidtransClient` | `None` | Optional custom client instance. Uses `get_client()` singleton if not provided. |

### Methods

#### `create_charge()`

Create a new payment charge via Midtrans Core API.

```python
payment, response = service.create_charge(
    payment_type,
    gross_amount,
    order_id=None,
    customer_details=None,
    item_details=None,
    payment_options=None,
    custom_expiry=None,
    notification_url=None,
    metadata=None,
    custom_fields=None,
    user=None,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `payment_type` | `str` | *required* | Payment type constant (e.g. `PaymentType.CREDIT_CARD`, `PaymentType.GOPAY`). |
| `gross_amount` | `int` | *required* | Total charge amount in IDR (smallest unit). |
| `order_id` | `str` | `None` | Custom order ID. Auto-generated as `ORDER-YYYYMMDDHHMMSS-XXXXXXXX` if not provided. |
| `customer_details` | `dict` | `None` | `{"first_name": "", "last_name": "", "email": "", "phone": ""}` |
| `item_details` | `list[dict]` | `None` | List of `{"id": "", "name": "", "price": 0, "quantity": 1}` |
| `payment_options` | `dict` | `None` | Payment-type-specific options (see below). |
| `custom_expiry` | `dict` | `None` | `{"expiry_duration": 60, "unit": "minute"}` |
| `notification_url` | `str` | `None` | Override notification webhook URL. |
| `metadata` | `dict` | `None` | Arbitrary metadata stored on the payment record. |
| `custom_fields` | `list[str]` | `None` | Up to 3 custom field values. |
| `user` | `User` | `None` | Django user instance to associate with the payment. |

**Returns:** `(MidtransPayment, dict)` — The created payment model instance and raw Midtrans API response.

**Payment Options by Type:**

| Payment Type | Options |
|-------------|---------|
| `credit_card` | `{"token_id": "...", "authentication": true}` |
| `bank_transfer` | `{"bank": "bca", "va_number": "..."}` |
| `gopay` | `{"callback_url": "..."}` |
| `shopeepay` | `{"callback_url": "..."}` |
| `qris` | `{"acquirer": "gopay"}` |
| `echannel` | `{"bill_info1": "Payment:", "bill_info2": "Online purchase"}` |
| `cstore` | `{"store": "indomaret"}` |

**Example:**

```python
from django_midtrans.services import PaymentService
from django_midtrans.constants import PaymentType

service = PaymentService()

payment, response = service.create_charge(
    payment_type=PaymentType.BANK_TRANSFER,
    gross_amount=100000,
    customer_details={
        "first_name": "John",
        "email": "john@example.com",
    },
    payment_options={"bank": "bca"},
    user=request.user,
)

print(payment.va_number)  # "1234567890"
```

---

#### `get_status()`

Fetch current payment status from Midtrans and update the local record.

```python
response = service.get_status(payment)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `payment` | `MidtransPayment` or `str` | Payment instance or `order_id` string. |

**Returns:** `dict` — Raw Midtrans status response. If a `MidtransPayment` instance was given, it is updated in-place.

---

#### `cancel_payment()`

Cancel a pending payment.

```python
payment, response = service.cancel_payment(payment)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `payment` | `MidtransPayment` or `str` | Payment instance or `order_id`. |

**Returns:** `(MidtransPayment, dict)`

---

#### `expire_payment()`

Force-expire a pending payment.

```python
payment, response = service.expire_payment(payment)
```

---

#### `capture_payment()`

Capture an authorized credit card payment.

```python
payment, response = service.capture_payment(payment, amount=None)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `payment` | `MidtransPayment` or `str` | *required* | Payment instance or `order_id`. |
| `amount` | `int` | `None` | Capture amount. Defaults to full `gross_amount`. |

---

#### `refund_payment()`

Refund a settled payment (full or partial).

```python
payment, refund, response = service.refund_payment(
    payment, amount, reason="", direct=False
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `payment` | `MidtransPayment` or `str` | *required* | Payment instance or `order_id`. |
| `amount` | `int` | *required* | Refund amount. |
| `reason` | `str` | `""` | Refund reason. |
| `direct` | `bool` | `False` | Use direct (online) refund endpoint. |

**Returns:** `(MidtransPayment, MidtransRefund, dict)`

---

#### `approve_payment()`

Approve a challenged (fraud-flagged) payment.

```python
payment, response = service.approve_payment(payment)
```

---

#### `deny_payment()`

Deny a challenged (fraud-flagged) payment.

```python
payment, response = service.deny_payment(payment)
```

---

## InvoiceService

Service for managing Midtrans invoices.

### Constructor

```python
InvoiceService(client=None)
```

### Methods

#### `create_invoice()`

Create and send an invoice via Midtrans.

```python
invoice, response = service.create_invoice(
    customer_name,
    customer_email,
    due_date,
    items,
    customer_phone="",
    customer_id="",
    notes="",
    order_id=None,
    invoice_number=None,
    user=None,
    metadata=None,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `customer_name` | `str` | *required* | Customer full name. |
| `customer_email` | `str` | *required* | Customer email address. |
| `due_date` | `date` | *required* | Invoice due date. |
| `items` | `list[dict]` | *required* | `[{"name": "...", "price": 10000, "quantity": 1}]` |
| `customer_phone` | `str` | `""` | Customer phone number. |
| `customer_id` | `str` | `""` | External customer ID. |
| `notes` | `str` | `""` | Invoice notes. |
| `order_id` | `str` | `None` | Auto-generated `INV-YYYYMMDD-XXXXXXXX` if omitted. |
| `invoice_number` | `str` | `None` | Auto-generated with `INVOICE_PREFIX` setting. |
| `user` | `User` | `None` | Django user to associate. |
| `metadata` | `dict` | `None` | Arbitrary metadata. |

**Returns:** `(MidtransInvoice, dict)`

---

#### `get_invoice_status()`

```python
response = service.get_invoice_status(invoice)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `invoice` | `MidtransInvoice` or `str` | Invoice instance or Midtrans invoice ID. |

---

#### `void_invoice()`

```python
invoice, response = service.void_invoice(invoice, reason="")
```

---

## SubscriptionService

Service for managing Midtrans subscriptions (recurring payments).

### Constructor

```python
SubscriptionService(client=None)
```

### Methods

#### `create_subscription()`

```python
subscription, response = service.create_subscription(
    name, amount, payment_type,
    token="", interval=1, interval_unit="month", max_interval=12,
    start_time=None, retry_interval=1, retry_interval_unit="day",
    retry_max_interval=3, customer_details=None,
    gopay_account_id="", user=None, metadata=None,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | *required* | Subscription name. |
| `amount` | `int` | *required* | Recurring charge amount. |
| `payment_type` | `str` | *required* | `PaymentType.CREDIT_CARD` or `PaymentType.GOPAY`. |
| `token` | `str` | `""` | Card token (for credit card subscriptions). |
| `gopay_account_id` | `str` | `""` | GoPay account ID (for GoPay subscriptions). |
| `interval` | `int` | `1` | Billing interval count. |
| `interval_unit` | `str` | `"month"` | `"day"`, `"week"`, or `"month"`. |
| `max_interval` | `int` | `12` | Max number of billing cycles. |

**Returns:** `(MidtransSubscription, dict)`

---

#### `get_subscription_status()`

```python
response = service.get_subscription_status(subscription)
```

#### `disable_subscription()`

```python
subscription, response = service.disable_subscription(subscription)
```

#### `enable_subscription()`

```python
subscription, response = service.enable_subscription(subscription)
```

#### `cancel_subscription()`

```python
subscription, response = service.cancel_subscription(subscription)
```

#### `update_subscription()`

```python
subscription, response = service.update_subscription(subscription, name=..., amount=..., schedule=...)
```
