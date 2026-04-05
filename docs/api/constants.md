# Constants

The `django_midtrans.constants` module defines all enumeration constants used throughout the package. Each class contains string constants and a `CHOICES` list compatible with Django model field choices.

---

## PaymentType

Payment method identifiers sent to Midtrans.

| Constant | Value | Label |
|----------|-------|-------|
| `CREDIT_CARD` | `"credit_card"` | Credit Card |
| `GOPAY` | `"gopay"` | GoPay |
| `SHOPEEPAY` | `"shopeepay"` | ShopeePay |
| `QRIS` | `"qris"` | QRIS |
| `OVO` | `"ovo"` | OVO |
| `DANA` | `"dana"` | DANA |
| `BANK_TRANSFER` | `"bank_transfer"` | Bank Transfer |
| `ECHANNEL` | `"echannel"` | Mandiri Bill |
| `CSTORE` | `"cstore"` | Convenience Store |
| `AKULAKU` | `"akulaku"` | Akulaku |
| `KREDIVO` | `"kredivo"` | Kredivo |

```python
from django_midtrans.constants import PaymentType

payment_type = PaymentType.BANK_TRANSFER  # "bank_transfer"
```

---

## BankType

Bank identifiers for Virtual Account (bank transfer) payments.

| Constant | Value | Label |
|----------|-------|-------|
| `BCA` | `"bca"` | BCA |
| `BNI` | `"bni"` | BNI |
| `BRI` | `"bri"` | BRI |
| `PERMATA` | `"permata"` | Permata |
| `CIMB` | `"cimb"` | CIMB |

```python
from django_midtrans.constants import BankType

bank = BankType.BCA  # "bca"
```

---

## TransactionStatus

Midtrans transaction lifecycle statuses.

| Constant | Value | Label | Description |
|----------|-------|-------|-------------|
| `PENDING` | `"pending"` | Pending | Waiting for customer payment. |
| `CAPTURE` | `"capture"` | Capture | Credit card captured (success for CC). |
| `SETTLEMENT` | `"settlement"` | Settlement | Payment settled (final success). |
| `DENY` | `"deny"` | Deny | Payment denied by bank or fraud check. |
| `CANCEL` | `"cancel"` | Cancel | Payment cancelled. |
| `EXPIRE` | `"expire"` | Expire | Payment expired (customer didn't pay in time). |
| `REFUND` | `"refund"` | Refund | Full refund issued. |
| `PARTIAL_REFUND` | `"partial_refund"` | Partial Refund | Partial refund issued. |
| `AUTHORIZE` | `"authorize"` | Authorize | Credit card authorized (pre-auth). |
| `FAILURE` | `"failure"` | Failure | Transaction failed. |

### Status Groups

```python
TransactionStatus.SUCCESS_STATUSES  # ["capture", "settlement"]
TransactionStatus.FAILED_STATUSES   # ["deny", "cancel", "expire", "failure"]
TransactionStatus.FINAL_STATUSES    # ["settlement", "deny", "cancel", "expire", "refund", "failure"]
```

---

## FraudStatus

Midtrans fraud detection result.

| Constant | Value | Label | Description |
|----------|-------|-------|-------------|
| `ACCEPT` | `"accept"` | Accept | Transaction accepted. |
| `CHALLENGE` | `"challenge"` | Challenge | Flagged for manual review. |
| `DENY` | `"deny"` | Deny | Denied by fraud detection. |

---

## InvoiceStatus

Invoice lifecycle statuses.

| Constant | Value | Label |
|----------|-------|-------|
| `DRAFT` | `"draft"` | Draft |
| `SENT` | `"sent"` | Sent |
| `PAID` | `"paid"` | Paid |
| `OVERDUE` | `"overdue"` | Overdue |
| `VOID` | `"void"` | Void |
| `PARTIAL` | `"partial"` | Partial |

---

## SubscriptionStatus

Subscription lifecycle statuses.

| Constant | Value | Label |
|----------|-------|-------|
| `ACTIVE` | `"active"` | Active |
| `INACTIVE` | `"inactive"` | Inactive |
| `DISABLED` | `"disabled"` | Disabled |
| `CANCELLED` | `"cancelled"` | Cancelled |

---

## NotificationStatus

Internal processing status for webhook notifications.

| Constant | Value | Label | Description |
|----------|-------|-------|-------------|
| `RECEIVED` | `"received"` | Received | Notification received but not yet processed. |
| `PROCESSED` | `"processed"` | Processed | Successfully processed and payment updated. |
| `FAILED` | `"failed"` | Failed | Processing failed (see error_message). |
| `DUPLICATE` | `"duplicate"` | Duplicate | Duplicate notification (already processed). |
| `INVALID_SIGNATURE` | `"invalid_signature"` | Invalid Signature | Signature verification failed. |

---

## Usage with Django Models

All constants include a `CHOICES` list for use with Django model `choices` parameter:

```python
from django.db import models
from django_midtrans.constants import PaymentType, TransactionStatus

class Order(models.Model):
    payment_type = models.CharField(
        max_length=30,
        choices=PaymentType.CHOICES,
    )
    status = models.CharField(
        max_length=30,
        choices=TransactionStatus.CHOICES,
        default=TransactionStatus.PENDING,
    )
```
