# Views

The `django_midtrans.views` module provides Django REST Framework views and viewsets for payment operations.

---

## ChargeView

**Endpoint:** `POST /charge/`
**Permission:** `IsAuthenticated`

Create a new payment charge via Midtrans Core API.

### Request Body

Uses `ChargeSerializer` for validation. See [Serializers](serializers.md) for full field details.

```json
{
    "payment_type": "bank_transfer",
    "gross_amount": 100000,
    "bank": "bca",
    "customer_details": {
        "first_name": "John",
        "email": "john@example.com"
    },
    "item_details": [
        {"name": "Product A", "price": 100000, "quantity": 1}
    ]
}
```

### Response

**201 Created** — Returns `PaymentSerializer` data:

```javascript
{
    "id": "550e8400-e29b-...",
    "order_id": "ORDER-20240101-ABC12345",
    "payment_type": "bank_transfer",
    "gross_amount": "100000.00",
    "transaction_status": "pending",
    "va_number": "1234567890"
}
```

**400 Bad Request** — Validation errors or Midtrans API errors.

---

## PaymentViewSet

**Base Endpoint:** `/payments/`
**Permission:** `IsAuthenticated`
**Type:** `ReadOnlyModelViewSet` (list + retrieve only, plus custom actions)

Non-staff users can only see their own payments. Staff users see all payments.

### Query Parameters (list)

| Parameter | Description |
|-----------|-------------|
| `payment_type` | Filter by payment type (e.g. `bank_transfer`). |
| `status` | Filter by transaction status (e.g. `pending`, `settlement`). |

### Actions

#### `GET /payments/`

List payments. Returns `PaymentListSerializer` data.

#### `GET /payments/{pk}/`

Retrieve payment detail. Returns `PaymentSerializer` data.

#### `GET /payments/{pk}/check_status/`

Fetch latest status from Midtrans API and update localpayment record.

**Response:**

```json
{
    "payment": { "...PaymentSerializer data..." },
    "midtrans_response": { "...raw Midtrans response..." }
}
```

#### `POST /payments/{pk}/cancel/`

Cancel a non-final payment. Returns 400 if payment is already in a final state.

#### `POST /payments/{pk}/expire/`

Force-expire a pending payment. Returns 400 if payment is not pending.

#### `POST /payments/{pk}/refund/`

Refund a paid payment. Request body:

```json
{
    "amount": 50000,
    "reason": "Customer request",
    "direct": false
}
```

**Response:**

```json
{
    "payment": { "...PaymentSerializer data..." },
    "refund": { "...RefundSerializer data..." }
}
```

#### `POST /payments/{pk}/capture/`

Capture an authorized credit card payment. Only available for `credit_card` payment type.

```json
{
    "amount": 100000
}
```

---

## NotificationView

**Endpoint:** `POST /notification/`
**Permission:** `AllowAny` (no authentication required)

Midtrans webhook notification handler. This endpoint must be publicly accessible for Midtrans to send payment status updates.

### Request Body

Raw JSON payload from Midtrans containing `order_id`, `transaction_status`, `signature_key`, etc.

### Response

**200 OK:**

```json
{
    "status": "ok",
    "notification_id": "uuid"
}
```

The handler automatically:
1. Verifies the signature
2. Creates a `MidtransNotification` record
3. Updates the related `MidtransPayment` status
4. Dispatches appropriate Django signals

---

## InvoiceListCreateView

**Endpoint:** `GET /invoices/` | `POST /invoices/`
**Permission:** `IsAuthenticated`

List invoices or create a new invoice via Midtrans Invoice API.

### Create Request Body

```json
{
    "customer_name": "John Doe",
    "customer_email": "john@example.com",
    "due_date": "2024-12-31",
    "items": [
        {"description": "Service Fee", "price": 500000, "quantity": 1}
    ],
    "notes": "Payment for consulting"
}
```

---

## InvoiceDetailView

**Endpoint:** `GET /invoices/{pk}/`
**Permission:** `IsAuthenticated`

Retrieve a single invoice.

---

## InvoiceVoidView

**Endpoint:** `POST /invoices/{pk}/void/`
**Permission:** `IsAuthenticated`

Void an invoice.

```json
{
    "reason": "Customer cancelled order"
}
```

---

## SubscriptionListCreateView

**Endpoint:** `GET /subscriptions/` | `POST /subscriptions/`
**Permission:** `IsAuthenticated`

List or create subscriptions.

### Create Request Body

```json
{
    "name": "Monthly Premium",
    "amount": 99000,
    "payment_type": "credit_card",
    "token": "card-token-from-frontend",
    "interval": 1,
    "interval_unit": "month",
    "max_interval": 12
}
```

---

## SubscriptionDetailView

**Endpoint:** `GET /subscriptions/{pk}/`
**Permission:** `IsAuthenticated`

Retrieve a single subscription.

---

## SubscriptionActionView

**Endpoint:** `POST /subscriptions/{pk}/{action_name}/`
**Permission:** `IsAuthenticated`

Perform actions on a subscription.

| Action | Description |
|--------|-------------|
| `disable` | Temporarily disable the subscription. |
| `enable` | Re-enable a disabled subscription. |
| `cancel` | Permanently cancel the subscription. |

---

## URL Configuration

Include in your `urls.py`:

```python
from django.urls import path, include

urlpatterns = [
    path("api/midtrans/", include("django_midtrans.urls")),
]
```

This registers all views above under `/api/midtrans/`.
