# Webhook Notifications

Midtrans sends HTTP POST notifications (webhooks) to your server when payment statuses change.

## Setup

### 1. Configure the Notification URL

In your Django settings:

```python
MIDTRANS = {
    # ...
    "NOTIFICATION_URL": "https://yourdomain.com/midtrans/api/notification/",
}
```

### 2. Include URLs

```python
# urls.py
urlpatterns = [
    path("midtrans/api/", include("django_midtrans.urls")),
]
```

The notification endpoint is automatically registered at `/midtrans/api/notification/`.

```{important}
The notification endpoint uses `AllowAny` permission — it does **not** require authentication. Security is enforced through **signature verification**.
```

## How It Works

```
Midtrans Server  ──POST──►  /midtrans/api/notification/
                                    │
                            NotificationView
                                    │
                            NotificationHandler
                                    │
                      ┌─────────────┼──────────────┐
                      │             │              │
              Verify Signature  Save Record   Fire Signal
```

1. **Midtrans** sends a POST with JSON payload containing `order_id`, `transaction_status`, `signature_key`, etc.
2. **NotificationView** receives it and delegates to `NotificationHandler`.
3. **NotificationHandler**:
   - Verifies the SHA-512 signature
   - Creates a `MidtransNotification` record
   - Updates the linked `MidtransPayment` status
   - Fires the appropriate Django signal

## Signature Verification

Every notification includes a `signature_key` computed as:

```
SHA512(order_id + status_code + gross_amount + server_key)
```

The handler verifies this automatically using `MidtransClient.verify_signature()`. If the signature is invalid, the notification is saved with `status="invalid_signature"` and no signal is fired.

## Notification Payload

Example payload from Midtrans:

```json
{
    "order_id": "ORDER-001",
    "transaction_id": "abc-123-def",
    "transaction_status": "settlement",
    "payment_type": "bank_transfer",
    "fraud_status": "accept",
    "status_code": "200",
    "gross_amount": "100000.00",
    "signature_key": "a1b2c3d4..."
}
```

## Notification Statuses

Each `MidtransNotification` record tracks its processing status:

| Status | Description |
|--------|-------------|
| `received` | Notification received, not yet processed |
| `processed` | Successfully processed and payment updated |
| `failed` | Processing failed (see `error_message`) |
| `duplicate` | Duplicate notification (already processed) |
| `invalid_signature` | Signature verification failed |

## Handling Notifications with Signals

The recommended way to react to payment events is through Django signals:

```python
# yourapp/signals.py
from django.dispatch import receiver
from django_midtrans.signals import payment_settled, payment_expired

@receiver(payment_settled)
def handle_payment_settled(sender, payment, notification, payload, **kwargs):
    """Called when a payment is successfully settled."""
    order = Order.objects.get(midtrans_payment=payment)
    order.status = "paid"
    order.save()
    send_confirmation_email(order)

@receiver(payment_expired)
def handle_payment_expired(sender, payment, notification, payload, **kwargs):
    """Called when a payment expires."""
    order = Order.objects.get(midtrans_payment=payment)
    order.status = "expired"
    order.save()
    # Optionally restore inventory
    for item in order.items.all():
        item.product.stock += item.quantity
        item.product.save()
```

See the [](signals.md) page for a complete list of available signals.

## Local Development with ngrok

Midtrans needs a publicly accessible URL for webhooks. Use [ngrok](https://ngrok.com/) during development:

```bash
# Start your Django server
python manage.py runserver

# In another terminal, expose it
ngrok http 8000
```

Then set the ngrok URL in your Midtrans dashboard:

```
https://abc123.ngrok-free.app/midtrans/api/notification/
```

Or configure it in settings:

```python
MIDTRANS = {
    "NOTIFICATION_URL": "https://abc123.ngrok-free.app/midtrans/api/notification/",
}
```

```{tip}
In sandbox mode, you can also use the Midtrans dashboard simulator to manually trigger notifications.
```

## Retry Behavior

Midtrans retries failed webhook deliveries. Your endpoint should:

1. **Return HTTP 200** quickly — even if processing takes time
2. **Handle duplicates** — the handler automatically marks them as `duplicate`
3. **Be idempotent** — the same notification may arrive more than once

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Notifications not arriving | Check the notification URL in Midtrans dashboard and your settings |
| Invalid signature errors | Verify `SERVER_KEY` matches your Midtrans account |
| 404 on notification URL | Ensure `django_midtrans.urls` is included in your URL config |
| Behind reverse proxy | Make sure your proxy passes the POST body correctly |
