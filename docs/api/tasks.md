# Tasks

The `django_midtrans.tasks` module provides Celery tasks for asynchronous payment processing and periodic maintenance.

All tasks use `@shared_task` and support automatic retry with exponential backoff for Midtrans API errors.

---

## Payment Status Tasks

### check_payment_status

Check and update the status of a single payment from Midtrans.

```python
from django_midtrans.tasks import check_payment_status

# Call async
check_payment_status.delay("ORDER-123")

# Call sync
result = check_payment_status("ORDER-123")
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `order_id` | `str` | The payment order ID to check. |

**Retry Policy:** 3 retries, 60s initial delay, exponential backoff.

**Returns:**

```python
{"order_id": "ORDER-123", "status": "settlement", "midtrans_status": "settlement"}
# or if already final:
{"order_id": "ORDER-123", "status": "settlement", "skipped": True}
# or if not found:
{"error": "Payment ORDER-123 not found"}
```

---

### check_pending_payments

Periodic task: Check status of all pending payments by dispatching individual `check_payment_status` tasks.

```python
from django_midtrans.tasks import check_pending_payments

# Run manually
check_pending_payments.delay()
```

**Returns:** `{"queued": 15}` — Number of status checks dispatched.

**Recommended Celery Beat schedule:** Every 5-15 minutes.

---

### expire_stale_payments

Periodic task: Expire payments that have passed their expiry time and are still pending.

```python
from django_midtrans.tasks import expire_stale_payments

expire_stale_payments.delay()
```

**Returns:** `{"expired": 3}` — Number of payments expired.

**Recommended Celery Beat schedule:** Every 5 minutes.

---

## Invoice Tasks

### check_overdue_invoices

Periodic task: Mark invoices as overdue if past due date and still in `draft` or `sent` status.

```python
from django_midtrans.tasks import check_overdue_invoices

check_overdue_invoices.delay()
```

**Returns:** `{"overdue": 2}` — Number of invoices marked overdue.

**Recommended Celery Beat schedule:** Once daily.

---

## Async Processing Tasks

### process_charge_async

Async payment charge creation. Useful for non-blocking charge processing.

```python
from django_midtrans.tasks import process_charge_async

result = process_charge_async.delay({
    "payment_type": "bank_transfer",
    "gross_amount": 100000,
    "payment_options": {"bank": "bca"},
    "customer_details": {"first_name": "John", "email": "john@example.com"},
})
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `charge_kwargs` | `dict` | Keyword arguments passed to `PaymentService.create_charge()`. |

**Retry Policy:** 3 retries, 30s initial delay, exponential backoff.

**Returns:**

```python
{
    "order_id": "ORDER-20240101-ABC12345",
    "transaction_status": "pending",
    "payment_id": "uuid-string",
}
```

---

### process_refund_async

Async refund processing.

```python
from django_midtrans.tasks import process_refund_async

process_refund_async.delay("ORDER-123", 50000, reason="Customer request", direct=False)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `order_id` | `str` | *required* | Payment order ID. |
| `amount` | `int` | *required* | Refund amount. |
| `reason` | `str` | `""` | Refund reason. |
| `direct` | `bool` | `False` | Use direct (online) refund. |

**Returns:**

```python
{
    "order_id": "ORDER-123",
    "refund_key": "refund-ORDER-123-abc12345",
    "refund_amount": "50000",
}
```

---

## Subscription Tasks

### sync_subscription_status

Periodic task: Sync all active/inactive subscription statuses from Midtrans.

```python
from django_midtrans.tasks import sync_subscription_status

sync_subscription_status.delay()
```

**Returns:** `{"synced": 5}` — Number of subscriptions with changed status.

**Recommended Celery Beat schedule:** Every hour.

---

## Celery Beat Configuration

Recommended schedule for all periodic tasks:

```python
# settings.py
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "midtrans-check-pending": {
        "task": "django_midtrans.tasks.check_pending_payments",
        "schedule": crontab(minute="*/10"),  # Every 10 minutes
    },
    "midtrans-expire-stale": {
        "task": "django_midtrans.tasks.expire_stale_payments",
        "schedule": crontab(minute="*/5"),  # Every 5 minutes
    },
    "midtrans-check-overdue-invoices": {
        "task": "django_midtrans.tasks.check_overdue_invoices",
        "schedule": crontab(hour=0, minute=30),  # Daily at 00:30
    },
    "midtrans-sync-subscriptions": {
        "task": "django_midtrans.tasks.sync_subscription_status",
        "schedule": crontab(minute=0),  # Every hour
    },
}
```

---

## Task Summary

| Task | Type | Retry | Schedule |
|------|------|-------|----------|
| `check_payment_status` | On-demand | 3x, backoff | — |
| `check_pending_payments` | Periodic | 1x | Every 10 min |
| `expire_stale_payments` | Periodic | 1x | Every 5 min |
| `check_overdue_invoices` | Periodic | 1x | Daily |
| `process_charge_async` | On-demand | 3x, backoff | — |
| `process_refund_async` | On-demand | 3x, backoff | — |
| `sync_subscription_status` | Periodic | 1x | Every hour |
