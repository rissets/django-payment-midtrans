# Signals

The `django_midtrans.signals` module provides Django signals dispatched during payment lifecycle events.

All signals send `sender` and keyword arguments. Connect handlers to react to payment state changes.

---

## Payment Signals

### payment_received

Dispatched when a new pending payment is created.

```python
from django_midtrans.signals import payment_received

@receiver(payment_received)
def on_payment_received(sender, payment, notification, **kwargs):
    print(f"New payment: {payment.order_id}")
```

| Argument | Type | Description |
|----------|------|-------------|
| `payment` | `MidtransPayment` | The payment instance. |
| `notification` | `MidtransNotification` | The notification that triggered this signal. |

---

### payment_settled

Dispatched when a payment is successfully settled or captured.

```python
from django_midtrans.signals import payment_settled

@receiver(payment_settled)
def on_payment_settled(sender, payment, notification, **kwargs):
    # Fulfill the order
    order = Order.objects.get(midtrans_order_id=payment.order_id)
    order.status = "paid"
    order.save()
```

---

### payment_denied

Dispatched when a payment is denied (fraud or bank rejection).

```python
from django_midtrans.signals import payment_denied

@receiver(payment_denied)
def on_payment_denied(sender, payment, notification, **kwargs):
    send_payment_denied_email(payment.customer_email)
```

---

### payment_cancelled

Dispatched when a payment is cancelled.

---

### payment_expired

Dispatched when a payment expires (not paid within time limit).

---

### payment_refunded

Dispatched when a payment is refunded (full or partial).

---

### payment_failed

Dispatched when a payment fails.

---

## Invoice Signals

### invoice_created

Dispatched when a new invoice is created.

### invoice_paid

Dispatched when an invoice is paid.

### invoice_voided

Dispatched when an invoice is voided.

---

## Subscription Signals

### subscription_created

Dispatched when a new subscription is created.

### subscription_charged

Dispatched when a subscription charge is processed.

### subscription_disabled

Dispatched when a subscription is disabled.

### subscription_cancelled

Dispatched when a subscription is cancelled.

---

## Signal Handler Example

```python
# myapp/signals.py
from django.dispatch import receiver
from django_midtrans.signals import (
    payment_settled,
    payment_expired,
    payment_refunded,
)


@receiver(payment_settled)
def handle_payment_success(sender, payment, notification, **kwargs):
    """Send confirmation email and fulfill order."""
    from myapp.models import Order
    from myapp.tasks import send_confirmation_email

    order = Order.objects.get(payment_order_id=payment.order_id)
    order.mark_as_paid()
    send_confirmation_email.delay(order.id)


@receiver(payment_expired)
def handle_payment_expired(sender, payment, notification, **kwargs):
    """Release reserved stock."""
    from myapp.models import Order

    order = Order.objects.get(payment_order_id=payment.order_id)
    order.release_stock()


@receiver(payment_refunded)
def handle_refund(sender, payment, notification, **kwargs):
    """Notify customer of refund."""
    from myapp.tasks import send_refund_email

    send_refund_email.delay(payment.customer_email, str(payment.refund_amount))
```

Register in your `AppConfig.ready()`:

```python
# myapp/apps.py
from django.apps import AppConfig

class MyAppConfig(AppConfig):
    name = "myapp"

    def ready(self):
        import myapp.signals  # noqa: F401
```

---

## Complete Signal Reference

| Signal | Trigger | Arguments |
|--------|---------|-----------|
| `payment_received` | New pending payment via webhook | `payment`, `notification` |
| `payment_settled` | Payment settled/captured | `payment`, `notification` |
| `payment_denied` | Payment denied | `payment`, `notification` |
| `payment_cancelled` | Payment cancelled | `payment`, `notification` |
| `payment_expired` | Payment expired | `payment`, `notification` |
| `payment_refunded` | Payment refunded | `payment`, `notification` |
| `payment_failed` | Payment failed | `payment`, `notification` |
| `invoice_created` | Invoice created | `invoice` |
| `invoice_paid` | Invoice paid | `invoice` |
| `invoice_voided` | Invoice voided | `invoice` |
| `subscription_created` | Subscription created | `subscription` |
| `subscription_charged` | Subscription charged | `subscription` |
| `subscription_disabled` | Subscription disabled | `subscription` |
| `subscription_cancelled` | Subscription cancelled | `subscription` |
