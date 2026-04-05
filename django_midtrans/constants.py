from django.utils.translation import gettext_lazy as _


class PaymentType:
    CREDIT_CARD = "credit_card"
    GOPAY = "gopay"
    SHOPEEPAY = "shopeepay"
    QRIS = "qris"
    OVO = "ovo"
    DANA = "dana"
    BANK_TRANSFER = "bank_transfer"
    ECHANNEL = "echannel"
    CSTORE = "cstore"
    AKULAKU = "akulaku"
    KREDIVO = "kredivo"

    CHOICES = [
        (CREDIT_CARD, _("Credit Card")),
        (GOPAY, _("GoPay")),
        (SHOPEEPAY, _("ShopeePay")),
        (QRIS, _("QRIS")),
        (OVO, _("OVO")),
        (DANA, _("DANA")),
        (BANK_TRANSFER, _("Bank Transfer")),
        (ECHANNEL, _("Mandiri Bill")),
        (CSTORE, _("Convenience Store")),
        (AKULAKU, _("Akulaku")),
        (KREDIVO, _("Kredivo")),
    ]


class BankType:
    BCA = "bca"
    BNI = "bni"
    BRI = "bri"
    PERMATA = "permata"
    CIMB = "cimb"

    CHOICES = [
        (BCA, _("BCA")),
        (BNI, _("BNI")),
        (BRI, _("BRI")),
        (PERMATA, _("Permata")),
        (CIMB, _("CIMB")),
    ]


class TransactionStatus:
    PENDING = "pending"
    CAPTURE = "capture"
    SETTLEMENT = "settlement"
    DENY = "deny"
    CANCEL = "cancel"
    EXPIRE = "expire"
    REFUND = "refund"
    PARTIAL_REFUND = "partial_refund"
    AUTHORIZE = "authorize"
    FAILURE = "failure"

    CHOICES = [
        (PENDING, _("Pending")),
        (CAPTURE, _("Capture")),
        (SETTLEMENT, _("Settlement")),
        (DENY, _("Deny")),
        (CANCEL, _("Cancel")),
        (EXPIRE, _("Expire")),
        (REFUND, _("Refund")),
        (PARTIAL_REFUND, _("Partial Refund")),
        (AUTHORIZE, _("Authorize")),
        (FAILURE, _("Failure")),
    ]

    SUCCESS_STATUSES = [CAPTURE, SETTLEMENT]
    FAILED_STATUSES = [DENY, CANCEL, EXPIRE, FAILURE]
    FINAL_STATUSES = [SETTLEMENT, DENY, CANCEL, EXPIRE, REFUND, FAILURE]


class FraudStatus:
    ACCEPT = "accept"
    CHALLENGE = "challenge"
    DENY = "deny"

    CHOICES = [
        (ACCEPT, _("Accept")),
        (CHALLENGE, _("Challenge")),
        (DENY, _("Deny")),
    ]


class InvoiceStatus:
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    VOID = "void"
    PARTIAL = "partial"

    CHOICES = [
        (DRAFT, _("Draft")),
        (SENT, _("Sent")),
        (PAID, _("Paid")),
        (OVERDUE, _("Overdue")),
        (VOID, _("Void")),
        (PARTIAL, _("Partial")),
    ]


class SubscriptionStatus:
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISABLED = "disabled"
    CANCELLED = "cancelled"

    CHOICES = [
        (ACTIVE, _("Active")),
        (INACTIVE, _("Inactive")),
        (DISABLED, _("Disabled")),
        (CANCELLED, _("Cancelled")),
    ]


class NotificationStatus:
    RECEIVED = "received"
    PROCESSED = "processed"
    FAILED = "failed"
    DUPLICATE = "duplicate"
    INVALID_SIGNATURE = "invalid_signature"

    CHOICES = [
        (RECEIVED, _("Received")),
        (PROCESSED, _("Processed")),
        (FAILED, _("Failed")),
        (DUPLICATE, _("Duplicate")),
        (INVALID_SIGNATURE, _("Invalid Signature")),
    ]
