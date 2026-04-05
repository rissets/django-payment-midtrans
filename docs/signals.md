# Signals Reference

`django_midtrans` fires Django signals at key lifecycle events. Connect receivers to react to payment, invoice, and subscription changes.

## Connecting a Signal

```python
# yourapp/signals.py
from django.dispatch import receiver
from django_midtrans.signals import payment_settled

@receiver(payment_settled)
def handle_settled(sender, payment, notification, payload, **kwargs):
    print(f"Payment {payment.order_id} settled!")
```

Register in your app config:

```python
# yourapp/apps.py
class YourAppConfig(AppConfig):
    name = "yourapp"

    def ready(self):
        import yourapp.signals  # noqa: F401
```

## Signal Arguments

All payment signals send the same keyword arguments:

| Argument | Type | Description |
|----------|------|-------------|
| `sender` | class | `NotificationHandler` class |
| `payment` | `MidtransPayment` | The updated payment instance |
| `notification` | `MidtransNotification` | The notification record |
| `payload` | `dict` | Raw webhook payload from Midtrans |

Invoice and subscription signals send:

| Argument | Type | Description |
|----------|------|-------------|
| `sender` | class | The service class that triggered the signal |
| `invoice` / `subscription` | Model instance | The relevant model |

## Payment Signals

| Signal | Fired When |
|--------|-----------|
| `payment_received` | A new pending payment is created |
| `payment_settled` | Payment is successfully settled or captured |
| `payment_denied` | Payment is denied by Midtrans or the bank |
| `payment_cancelled` | Payment is cancelled |
| `payment_expired` | Payment expires (customer didn't pay in time) |
| `payment_refunded` | Payment is refunded (full or partial) |
| `payment_failed` | Payment fails for any other reason |

### Usage Examples

```python
from django_midtrans.signals import (
    payment_received,
    payment_settled,
    payment_denied,
    payment_cancelled,
    payment_expired,
    payment_refunded,
    payment_failed,
)

@receiver(payment_received)
def on_payment_received(sender, payment, notification, payload, **kwargs):
    """New payment is pending — show customer waiting instructions."""
    send_payment_instructions(payment)

@receiver(payment_settled)
def on_payment_settled(sender, payment, notification, payload, **kwargs):
    """Payment confirmed — fulfill the order."""
    order = Order.objects.get(midtrans_payment=payment)
    order.status = "paid"
    order.save()
    send_receipt_email(order)

@receiver(payment_denied)
def on_payment_denied(sender, payment, notification, payload, **kwargs):
    """Payment denied by bank/fraud check."""
    log_denied_payment(payment)

@receiver(payment_cancelled)
def on_payment_cancelled(sender, payment, notification, payload, **kwargs):
    """Payment was cancelled."""
    restore_stock(payment)

@receiver(payment_expired)
def on_payment_expired(sender, payment, notification, payload, **kwargs):
    """Payment expired — restore inventory."""
    restore_stock(payment)

@receiver(payment_refunded)
def on_payment_refunded(sender, payment, notification, payload, **kwargs):
    """Refund processed."""
    send_refund_confirmation(payment)

@receiver(payment_failed)
def on_payment_failed(sender, payment, notification, payload, **kwargs):
    """Payment failed."""
    notify_support_team(payment)
```

## Invoice Signals

| Signal | Fired When |
|--------|-----------|
| `invoice_created` | A new invoice is created |
| `invoice_paid` | Invoice payment is confirmed |
| `invoice_voided` | Invoice is voided/cancelled |

```python
from django_midtrans.signals import invoice_created, invoice_paid, invoice_voided

@receiver(invoice_paid)
def on_invoice_paid(sender, invoice, **kwargs):
    send_invoice_receipt(invoice)
```

## Subscription Signals

| Signal | Fired When |
|--------|-----------|
| `subscription_created` | A new subscription is created |
| `subscription_charged` | Recurring payment charged successfully |
| `subscription_disabled` | Subscription is disabled (paused) |
| `subscription_cancelled` | Subscription is permanently cancelled |

```python
from django_midtrans.signals import subscription_created, subscription_cancelled

@receiver(subscription_cancelled)
def on_subscription_cancelled(sender, subscription, **kwargs):
    revoke_premium_access(subscription.user)
```

## All Signals at a Glance

| Signal | Category | Arguments |
|--------|----------|-----------|
| `payment_received` | Payment | payment, notification, payload |
| `payment_settled` | Payment | payment, notification, payload |
| `payment_denied` | Payment | payment, notification, payload |
| `payment_cancelled` | Payment | payment, notification, payload |
| `payment_expired` | Payment | payment, notification, payload |
| `payment_refunded` | Payment | payment, notification, payload |
| `payment_failed` | Payment | payment, notification, payload |
| `invoice_created` | Invoice | invoice |
| `invoice_paid` | Invoice | invoice |
| `invoice_voided` | Invoice | invoice |
| `subscription_created` | Subscription | subscription |
| `subscription_charged` | Subscription | subscription |
| `subscription_disabled` | Subscription | subscription |
| `subscription_cancelled` | Subscription | subscription |
