# Serializers

The `django_midtrans.serializers` module provides Django REST Framework serializers for all API endpoints.

---

## Payment Serializers

### PaymentSerializer

Full payment detail serializer. Used for single payment responses.

**Model:** `MidtransPayment`

| Field | Type | Notes |
|-------|------|-------|
| `id` | `UUID` | Read-only. |
| `order_id` | `str` | |
| `transaction_id` | `str` | |
| `payment_type` | `str` | |
| `bank` | `str` | |
| `gross_amount` | `Decimal` | |
| `currency` | `str` | |
| `transaction_status` | `str` | |
| `fraud_status` | `str` | |
| `status_code` | `str` | |
| `status_message` | `str` | |
| `customer_first_name` | `str` | |
| `customer_last_name` | `str` | |
| `customer_email` | `str` | |
| `customer_phone` | `str` | |
| `va_number` | `str` | Bank transfer VA number. |
| `bill_key` | `str` | Mandiri bill key. |
| `biller_code` | `str` | Mandiri biller code. |
| `payment_code` | `str` | Convenience store code. |
| `redirect_url` | `str` | 3DS redirect URL. |
| `deeplink_url` | `str` | GoPay/ShopeePay deeplink. |
| `qr_string` | `str` | QRIS QR data. |
| `transaction_time` | `datetime` | |
| `settlement_time` | `datetime` | |
| `expiry_time` | `datetime` | |
| `refund_amount` | `Decimal` | |
| `net_amount` | `Decimal` | Computed: `gross_amount - refund_amount`. |
| `metadata` | `dict` | |
| `custom_field1` | `str` | |
| `custom_field2` | `str` | |
| `custom_field3` | `str` | |
| `items` | `list` | Nested `PaymentItemSerializer`. |
| `is_paid` | `bool` | |
| `is_pending` | `bool` | |
| `is_failed` | `bool` | |
| `is_expired` | `bool` | |
| `created_at` | `datetime` | |
| `updated_at` | `datetime` | |

All fields are **read-only**.

---

### PaymentListSerializer

Compact payment list serializer. Used for list endpoints.

| Field | Type |
|-------|------|
| `id` | `UUID` |
| `order_id` | `str` |
| `payment_type` | `str` |
| `gross_amount` | `Decimal` |
| `transaction_status` | `str` |
| `customer_email` | `str` |
| `is_paid` | `bool` |
| `created_at` | `datetime` |

---

### PaymentItemSerializer

**Model:** `MidtransPaymentItem`

| Field | Type |
|-------|------|
| `id` | `UUID` |
| `item_id` | `str` |
| `name` | `str` |
| `price` | `Decimal` |
| `quantity` | `int` |
| `brand` | `str` |
| `category` | `str` |
| `merchant_name` | `str` |
| `url` | `str` |
| `subtotal` | `Decimal` |

---

## Input Serializers

### ChargeSerializer

Input serializer for creating a payment charge.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `payment_type` | `ChoiceField` | Yes | One of the `PaymentType` constants. |
| `gross_amount` | `int` | Yes | Amount in IDR (min: 1). |
| `order_id` | `str` | No | Max 50 chars. Auto-generated if omitted. |
| `bank` | `ChoiceField` | Conditional | Required for `bank_transfer`. Values: `bca`, `bni`, `bri`, `permata`, `cimb`. |
| `token_id` | `str` | Conditional | Required for `credit_card`. Card token from frontend tokenization. |
| `callback_url` | `URL` | No | For GoPay/ShopeePay. |
| `store` | `ChoiceField` | Conditional | Required for `cstore`. Values: `indomaret`, `alfamart`. |
| `qris_acquirer` | `ChoiceField` | No | Default: `gopay`. Options: `gopay`, `airpay`. |
| `customer_details` | `object` | No | Nested `CustomerDetailInputSerializer`. |
| `item_details` | `list` | No | Nested `ItemDetailInputSerializer`. Sum must equal `gross_amount`. |
| `custom_expiry` | `object` | No | Nested `CustomExpiryInputSerializer`. |
| `notification_url` | `URL` | No | Override webhook URL. |
| `metadata` | `dict` | No | Arbitrary metadata. |
| `custom_fields` | `list[str]` | No | Max 3 items, each max 255 chars. |

**Validation Rules:**
- `token_id` is required when `payment_type` is `credit_card`.
- `bank` is required when `payment_type` is `bank_transfer`.
- `store` is required when `payment_type` is `cstore`.
- If `item_details` is provided, the sum of `price × quantity` must equal `gross_amount`.

---

### CustomerDetailInputSerializer

| Field | Type | Required | Default |
|-------|------|----------|---------|
| `first_name` | `str` | No | `""` |
| `last_name` | `str` | No | `""` |
| `email` | `EmailField` | No | `""` |
| `phone` | `str` | No | `""` |

---

### ItemDetailInputSerializer

| Field | Type | Required | Default |
|-------|------|----------|---------|
| `id` | `str` | No | `""` |
| `name` | `str` | Yes | — |
| `price` | `int` | Yes | — |
| `quantity` | `int` | No | `1` |
| `brand` | `str` | No | `""` |
| `category` | `str` | No | `""` |
| `merchant_name` | `str` | No | `""` |
| `url` | `URL` | No | `""` |

---

### CustomExpiryInputSerializer

| Field | Type | Required | Default |
|-------|------|----------|---------|
| `expiry_duration` | `int` | Yes | — |
| `unit` | `ChoiceField` | No | `"minute"` |

Options for `unit`: `second`, `minute`, `hour`, `day`.

---

## Refund Serializers

### RefundSerializer

Read-only serializer for refund records.

| Field | Type |
|-------|------|
| `id` | `UUID` |
| `refund_key` | `str` |
| `amount` | `Decimal` |
| `reason` | `str` |
| `is_direct` | `bool` |
| `status` | `str` |
| `status_code` | `str` |
| `status_message` | `str` |
| `created_at` | `datetime` |

### RefundInputSerializer

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `amount` | `int` | Yes | — | Must not exceed `payment.net_amount`. |
| `reason` | `str` | No | `""` | — |
| `direct` | `bool` | No | `False` | Use direct (online) refund. |

---

## Notification Serializers

### NotificationSerializer

Read-only serializer for notification records.

| Field | Type |
|-------|------|
| `id` | `UUID` |
| `order_id` | `str` |
| `transaction_id` | `str` |
| `transaction_status` | `str` |
| `fraud_status` | `str` |
| `payment_type` | `str` |
| `status_code` | `str` |
| `gross_amount` | `str` |
| `status` | `str` |
| `error_message` | `str` |
| `created_at` | `datetime` |

---

## Invoice Serializers

### InvoiceSerializer

Full invoice serializer with nested items.

| Field | Type |
|-------|------|
| `id` | `UUID` |
| `invoice_number` | `str` |
| `order_id` | `str` |
| `midtrans_invoice_id` | `str` |
| `status` | `str` |
| `customer_name` | `str` |
| `customer_email` | `str` |
| `customer_phone` | `str` |
| `customer_id` | `str` |
| `total_amount` | `Decimal` |
| `currency` | `str` |
| `due_date` | `date` |
| `paid_at` | `datetime` |
| `notes` | `str` |
| `void_reason` | `str` |
| `items` | `list` |
| `is_overdue` | `bool` |
| `metadata` | `dict` |
| `created_at` | `datetime` |
| `updated_at` | `datetime` |

### CreateInvoiceSerializer

| Field | Type | Required |
|-------|------|----------|
| `customer_name` | `str` | Yes |
| `customer_email` | `EmailField` | Yes |
| `customer_phone` | `str` | No |
| `customer_id` | `str` | No |
| `due_date` | `DateField` | Yes |
| `items` | `list[InvoiceItemInput]` | Yes (min 1) |
| `notes` | `str` | No |
| `order_id` | `str` | No |
| `invoice_number` | `str` | No |
| `metadata` | `dict` | No |

### VoidInvoiceSerializer

| Field | Type | Required | Default |
|-------|------|----------|---------|
| `reason` | `str` | No | `""` |

---

## Subscription Serializers

### SubscriptionSerializer

Full subscription serializer. All fields are read-only.

| Field | Type |
|-------|------|
| `id` | `UUID` |
| `midtrans_subscription_id` | `str` |
| `name` | `str` |
| `payment_type` | `str` |
| `amount` | `Decimal` |
| `currency` | `str` |
| `interval` | `int` |
| `interval_unit` | `str` |
| `max_interval` | `int` |
| `start_time` | `datetime` |
| `current_interval` | `int` |
| `status` | `str` |
| `customer_first_name` | `str` |
| `customer_last_name` | `str` |
| `customer_email` | `str` |
| `customer_phone` | `str` |
| `schedule_display` | `str` |
| `metadata` | `dict` |
| `created_at` | `datetime` |
| `updated_at` | `datetime` |

### CreateSubscriptionSerializer

| Field | Type | Required | Default |
|-------|------|----------|---------|
| `name` | `str` | Yes | — |
| `amount` | `int` | Yes | — |
| `payment_type` | `ChoiceField` | Yes | — |
| `token` | `str` | Conditional | `""` |
| `gopay_account_id` | `str` | Conditional | `""` |
| `interval` | `int` | No | `1` |
| `interval_unit` | `ChoiceField` | No | `"month"` |
| `max_interval` | `int` | No | `12` |
| `start_time` | `datetime` | No | — |
| `retry_interval` | `int` | No | `1` |
| `retry_interval_unit` | `ChoiceField` | No | `"day"` |
| `retry_max_interval` | `int` | No | `3` |
| `customer_details` | `object` | No | — |
| `metadata` | `dict` | No | — |

**Validation:**
- `token` is required when `payment_type` is `credit_card`.
- `gopay_account_id` is required when `payment_type` is `gopay`.
