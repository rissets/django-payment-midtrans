# Client

The `django_midtrans.client` module provides a low-level HTTP client for direct Midtrans Core API communication.

---

## MidtransClient

Low-level HTTP client for Midtrans Core API. Thread-safe, stateless — reuse a single instance.

### Constructor

```python
MidtransClient(server_key=None, is_production=None)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `server_key` | `str` | `None` | Midtrans server key. Uses `MIDTRANS_SERVER_KEY` from settings if not provided. |
| `is_production` | `bool` | `None` | If `True`, uses production API. If `None`, reads from `MIDTRANS_IS_PRODUCTION` setting. |

**Base URLs:**
- Production: `https://api.midtrans.com`
- Sandbox: `https://api.sandbox.midtrans.com`

---

### Core Payment API

#### `charge(payload)`

Create a payment charge.

```python
response = client.charge({
    "payment_type": "bank_transfer",
    "transaction_details": {
        "order_id": "ORDER-123",
        "gross_amount": 100000,
    },
    "bank_transfer": {"bank": "bca"},
})
```

**Returns:** `dict` — Raw Midtrans API response.

---

#### `get_status(order_id)`

Get transaction status.

```python
response = client.get_status("ORDER-123")
```

---

#### `get_status_b2b(order_id)`

Get B2B transaction status.

```python
response = client.get_status_b2b("ORDER-123")
```

---

#### `cancel(order_id)`

Cancel a transaction.

```python
response = client.cancel("ORDER-123")
```

---

#### `expire(order_id)`

Expire a pending transaction.

```python
response = client.expire("ORDER-123")
```

---

#### `capture(transaction_id, gross_amount)`

Capture an authorized credit card payment.

```python
response = client.capture("txn-uuid", 100000)
```

---

#### `refund(order_id, refund_key, amount, reason="")`

Refund a transaction.

```python
response = client.refund("ORDER-123", "refund-key-1", 50000, "Customer request")
```

---

#### `direct_refund(order_id, refund_key, amount, reason="")`

Direct (online) refund — faster for certain payment types.

```python
response = client.direct_refund("ORDER-123", "refund-key-1", 50000)
```

---

#### `approve(order_id)`

Approve a fraud-challenged transaction.

```python
response = client.approve("ORDER-123")
```

---

#### `deny(order_id)`

Deny a fraud-challenged transaction.

```python
response = client.deny("ORDER-123")
```

---

### Card API

#### `get_card_token(card_number, card_exp_month, card_exp_year, card_cvv, client_key=None)`

Tokenize a credit card (server-side — typically done client-side via MidtransNew3ds).

---

#### `register_card(card_number, card_exp_month, card_exp_year, client_key=None)`

Register a card for recurring use.

---

#### `point_inquiry(token_id)`

Query reward points balance for a tokenized card.

---

#### `get_bin(bin_number)`

Get card BIN (Bank Identification Number) metadata.

```python
response = client.get_bin("411111")
```

---

### GoPay Tokenization API

#### `create_pay_account(payload)`

Link a GoPay account.

```python
response = client.create_pay_account({
    "payment_type": "gopay",
    "gopay_partner": {
        "phone_number": "081234567890",
        "redirect_url": "https://example.com/callback",
    },
})
```

---

#### `get_pay_account(account_id)`

Get linked GoPay account status.

---

#### `unbind_pay_account(account_id)`

Unlink a GoPay account.

---

### Subscription API

#### `create_subscription(payload)`

Create a recurring subscription.

```python
response = client.create_subscription({
    "name": "Monthly Premium",
    "amount": "99000",
    "currency": "IDR",
    "payment_type": "credit_card",
    "token": "card-token",
    "schedule": {
        "interval": 1,
        "interval_unit": "month",
        "max_interval": 12,
    },
})
```

---

#### `get_subscription(subscription_id)`

Get subscription details.

---

#### `disable_subscription(subscription_id)`

Temporarily disable a subscription.

---

#### `enable_subscription(subscription_id)`

Re-enable a disabled subscription.

---

#### `cancel_subscription(subscription_id)`

Permanently cancel a subscription.

---

#### `update_subscription(subscription_id, payload)`

Update subscription details (name, amount, schedule).

---

### Invoice API

#### `create_invoice(payload)`

Create an invoice via Midtrans Invoice API.

---

#### `get_invoice(invoice_id)`

Get invoice details.

---

#### `void_invoice(invoice_id, void_reason="")`

Void an invoice.

---

### Signature Verification

#### `verify_signature(order_id, status_code, gross_amount, signature_key, server_key=None)`

Verify a Midtrans notification signature using SHA-512.

```python
is_valid = MidtransClient.verify_signature(
    order_id="ORDER-123",
    status_code="200",
    gross_amount="100000.00",
    signature_key="abc123...",
)
```

This is a **static method** — can be called without an instance.

**Signature formula:** `SHA512(order_id + status_code + gross_amount + server_key)`

---

### Error Handling

All API methods may raise exceptions from `django_midtrans.exceptions`:

| Exception | HTTP Status | Description |
|-----------|-------------|-------------|
| `MidtransAuthenticationError` | 401 | Invalid server key. |
| `MidtransDuplicateOrderError` | 406 | Order ID already used. |
| `MidtransRateLimitError` | 429 | Too many requests. |
| `MidtransValidationError` | 400 | Invalid request payload. |
| `MidtransAPIError` | 4xx/5xx | General API error. |

---

## get_client()

Module-level convenience function returning a singleton `MidtransClient` instance.

```python
from django_midtrans.client import get_client

client = get_client()
response = client.get_status("ORDER-123")
```

The singleton is created on first call using the default settings. This is the same client used internally by `PaymentService`, `InvoiceService`, and `SubscriptionService`.
