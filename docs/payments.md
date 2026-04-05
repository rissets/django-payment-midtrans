# Payment Methods

All payments are created through `PaymentService.create_charge()`. Each payment method returns different response data.

## Credit Card (3DS)

Credit card payments require **client-side tokenization** using the Midtrans JavaScript SDK before sending to the backend.

### Frontend: Tokenize Card

```html
<script src="https://api.sandbox.midtrans.com/v2/assets/js/midtrans-new-3ds.min.js"></script>
<script>
// Get card token from Midtrans
MidtransNew3ds.getCardToken({
    card_number: '4811111111111114',
    card_exp_month: '12',
    card_exp_year: '2028',
    card_cvv: '123',
    client_key: 'SB-Mid-client-xxxx'  // Your client key
}, {
    onSuccess: function(response) {
        // Send response.token_id to your backend
        chargeWithToken(response.token_id);
    },
    onFailure: function(response) {
        console.error('Tokenization failed:', response);
    }
});
</script>
```

### Backend: Create Charge

```python
from django_midtrans.services import PaymentService

service = PaymentService()
payment = service.create_charge(
    payment_type="credit_card",
    gross_amount=100000,
    order_id="CC-001",
    token_id="521111-1117-abc123-token",  # From frontend
    customer_details={
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        "phone": "081234567890",
    },
    item_details=[
        {"id": "ITEM-1", "name": "Product", "price": 100000, "quantity": 1},
    ],
)
```

### Response Fields

| Field | Description |
|-------|-------------|
| `payment.redirect_url` | 3DS authentication URL (if 3DS is required) |
| `payment.transaction_status` | `"capture"` (direct) or `"pending"` (needs 3DS) |

### 3DS Authentication Flow

If `payment.redirect_url` is set, the customer needs to complete 3DS:

```javascript
MidtransNew3ds.authenticate(payment.redirect_url, {
    performAuthentication: function(redirect_url) {
        // Open 3DS page in iframe
        document.getElementById('3ds-iframe').src = redirect_url;
    },
    onSuccess: function(response) {
        // Payment successful
    },
    onFailure: function(response) {
        // Authentication failed
    },
    onPending: function(response) {
        // Still processing
    }
});
```

### Sandbox Test Cards

| Card Number | Scenario |
|-------------|----------|
| `4811 1111 1111 1114` | 3DS Success |
| `4511 1111 1111 1117` | 3DS Challenge (OTP: `112233`) |
| `4211 1111 1111 1110` | Non-3DS Success |
| `4911 1111 1111 1113` | Fraud Denied |

---

## Bank Transfer (Virtual Account)

Generates a Virtual Account number for the customer to transfer to.

### Supported Banks

| Bank | Code | Description |
|------|------|-------------|
| BCA | `bca` | BCA Virtual Account |
| BNI | `bni` | BNI Virtual Account |
| BRI | `bri` | BRI Virtual Account |
| Permata | `permata` | Permata Virtual Account |
| CIMB | `cimb` | CIMB Niaga Virtual Account |

### Create Charge

```python
payment = service.create_charge(
    payment_type="bank_transfer",
    gross_amount=200000,
    order_id="VA-001",
    bank="bca",
    customer_details={
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        "phone": "081234567890",
    },
)

print(payment.va_number)          # "1234567890123456"
print(payment.bank)               # "bca"
print(payment.transaction_status) # "pending"
print(payment.expiry_time)        # When VA expires
```

### Response Fields

| Field | Description |
|-------|-------------|
| `payment.va_number` | Virtual Account number for customer to pay |
| `payment.bank` | Bank code |
| `payment.expiry_time` | When the VA expires |

---

## Mandiri Bill Payment (E-Channel)

Uses Mandiri's biller code + bill key system.

```python
payment = service.create_charge(
    payment_type="echannel",
    gross_amount=150000,
    order_id="MANDIRI-001",
    customer_details={...},
)

print(payment.bill_key)     # "12345678"
print(payment.biller_code)  # "70012"
```

### Response Fields

| Field | Description |
|-------|-------------|
| `payment.bill_key` | Mandiri bill key for payment |
| `payment.biller_code` | Mandiri biller code |

---

## E-Wallets

### GoPay

```python
payment = service.create_charge(
    payment_type="gopay",
    gross_amount=50000,
    order_id="GOPAY-001",
    customer_details={...},
)

print(payment.deeplink_url)  # Opens GoPay app
print(payment.qr_string)     # Raw QR data
```

### ShopeePay

```python
payment = service.create_charge(
    payment_type="shopeepay",
    gross_amount=50000,
    order_id="SPAY-001",
    customer_details={...},
)

# payment.redirect_url → Redirects to ShopeePay app/page
```

### DANA

```python
payment = service.create_charge(
    payment_type="dana",
    gross_amount=50000,
    order_id="DANA-001",
    customer_details={...},
)

# payment.redirect_url → Redirects to DANA app/page
```

### Response Fields (E-Wallets)

| Field | Description |
|-------|-------------|
| `payment.deeplink_url` | Deep link to open e-wallet app (GoPay) |
| `payment.redirect_url` | Redirect URL for web-based checkout (ShopeePay, DANA) |
| `payment.qr_string` | Raw QR code data string |

---

## QRIS

Universal QR code payment accepted by all QRIS-compatible e-wallets.

```python
payment = service.create_charge(
    payment_type="qris",
    gross_amount=75000,
    order_id="QRIS-001",
    customer_details={...},
)

qr_image_url = None
for action in payment.charge_response.get("actions", []):
    if action.get("name") == "generate-qr-code":
        qr_image_url = action["url"]
        break

qr_string = payment.charge_response.get("qr_string", "")
```

### Response Fields

| Field | Description |
|-------|-------------|
| `charge_response["actions"]` | Contains QR image URL |
| `charge_response["qr_string"]` | Raw EMV QR string for rendering |

---

## Convenience Store

Over-the-counter payment at retail stores.

### Supported Stores

| Store | Code |
|-------|------|
| Indomaret | `indomaret` |
| Alfamart | `alfamart` |

### Create Charge

```python
payment = service.create_charge(
    payment_type="cstore",
    gross_amount=100000,
    order_id="CSTORE-001",
    store="indomaret",
    customer_details={...},
)

print(payment.payment_code)  # Show this code at the counter
```

### Response Fields

| Field | Description |
|-------|-------------|
| `payment.payment_code` | Payment code to show at the counter |
| `charge_response["merchant_id"]` | Merchant ID (for Indomaret) |
| `charge_response["store"]` | Store name |

---

## Pay Later

### Akulaku

```python
payment = service.create_charge(
    payment_type="akulaku",
    gross_amount=500000,
    order_id="AKULAKU-001",
    customer_details={...},
)

# payment.redirect_url → Redirects to Akulaku installment page
```

---

## Payment Operations

After creating a payment, you can perform these operations:

### Check Status

```python
payment = service.get_status("ORDER-001")
print(payment.transaction_status)  # "settlement", "pending", etc.
```

### Cancel Payment

```python
payment = service.cancel_payment("ORDER-001")
```

### Expire Payment

```python
payment = service.expire_payment("ORDER-001")
```

### Refund Payment

```python
refund = service.refund_payment(
    order_id="ORDER-001",
    amount=50000,             # Partial refund
    reason="Customer request",
)
```

### Capture Payment (Credit Card)

For pre-authorized credit card transactions:

```python
payment = service.capture_payment(
    transaction_id="abc-123-def",
    gross_amount=100000,
)
```
