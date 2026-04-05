# Exceptions

The `django_midtrans.exceptions` module defines exception classes for Midtrans API errors.

All exceptions inherit from `MidtransError`.

---

## Exception Hierarchy

```
MidtransError (base)
├── MidtransAPIError (general API errors)
├── MidtransAuthenticationError (401)
├── MidtransValidationError (400)
├── MidtransDuplicateOrderError (406)
├── MidtransRateLimitError (429)
└── MidtransSignatureError (403)
```

---

## MidtransError

Base exception for all Midtrans errors.

```python
class MidtransError(Exception):
    message: str         # Error message
    status_code: int     # HTTP status code (may be None)
    data: dict           # Raw API response data
```

### Constructor

```python
MidtransError(message="", status_code=None, data=None)
```

---

## MidtransAPIError

General API error for non-specific HTTP errors (4xx/5xx).

```python
from django_midtrans.exceptions import MidtransAPIError

try:
    response = client.charge(payload)
except MidtransAPIError as e:
    print(e.message)      # "API error 500"
    print(e.status_code)  # 500
    print(e.data)         # {"status_code": "500", "status_message": "..."}
```

---

## MidtransAuthenticationError

Raised when the server key is invalid or missing (HTTP 401).

```python
from django_midtrans.exceptions import MidtransAuthenticationError

try:
    client.charge(payload)
except MidtransAuthenticationError:
    print("Check your MIDTRANS_SERVER_KEY setting")
```

| Attribute | Default |
|-----------|---------|
| `message` | `"Authentication failed"` |
| `status_code` | `401` |

---

## MidtransValidationError

Raised for invalid request payloads (HTTP 400).

```python
from django_midtrans.exceptions import MidtransValidationError

try:
    client.charge({"payment_type": "invalid"})
except MidtransValidationError as e:
    print(e.message)  # "Validation error"
    print(e.data)     # {"status_code": "400", "validation_messages": [...]}
```

| Attribute | Default |
|-----------|---------|
| `message` | `"Validation error"` |
| `status_code` | `400` |

---

## MidtransDuplicateOrderError

Raised when the order ID has already been used (HTTP 406).

```python
from django_midtrans.exceptions import MidtransDuplicateOrderError

try:
    client.charge(payload)
except MidtransDuplicateOrderError:
    print("Generate a new order_id and retry")
```

| Attribute | Default |
|-----------|---------|
| `message` | `"Duplicate order ID"` |
| `status_code` | `406` |

---

## MidtransRateLimitError

Raised when the API rate limit is exceeded (HTTP 429).

```python
from django_midtrans.exceptions import MidtransRateLimitError

try:
    client.charge(payload)
except MidtransRateLimitError:
    time.sleep(60)  # Wait and retry
```

| Attribute | Default |
|-----------|---------|
| `message` | `"Rate limit exceeded"` |
| `status_code` | `429` |

---

## MidtransSignatureError

Raised when a webhook notification signature verification fails.

```python
from django_midtrans.exceptions import MidtransSignatureError

try:
    handler.handle(notification_data)
except MidtransSignatureError:
    print("Notification signature is invalid — potential tampering")
```

| Attribute | Default |
|-----------|---------|
| `message` | `"Invalid signature"` |
| `status_code` | `403` |

---

## Error Handling Best Practice

```python
from django_midtrans.exceptions import (
    MidtransError,
    MidtransAuthenticationError,
    MidtransDuplicateOrderError,
    MidtransRateLimitError,
    MidtransValidationError,
)
from django_midtrans.services import PaymentService

service = PaymentService()

try:
    payment, response = service.create_charge(
        payment_type="bank_transfer",
        gross_amount=100000,
        payment_options={"bank": "bca"},
    )
except MidtransAuthenticationError:
    # Invalid API credentials
    logger.critical("Midtrans authentication failed — check server key")
except MidtransDuplicateOrderError:
    # Order ID collision — regenerate and retry
    logger.warning("Duplicate order ID, retrying with new ID")
except MidtransValidationError as e:
    # Bad request payload
    logger.error("Validation: %s — %s", e.message, e.data)
except MidtransRateLimitError:
    # Back off and retry
    logger.warning("Rate limited, will retry later")
except MidtransError as e:
    # Catch-all for any Midtrans error
    logger.error("Midtrans error: %s (HTTP %s)", e.message, e.status_code)
```
