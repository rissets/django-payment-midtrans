# Celery & Async Tasks

`django_midtrans` includes Celery tasks for background payment processing and periodic maintenance.

## Setup

### 1. Install Celery

```bash
pip install celery[redis]
```

### 2. Configure Celery in Your Project

```python
# config/celery.py
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
```

```python
# config/__init__.py
from .celery import app as celery_app

__all__ = ["celery_app"]
```

### 3. Configure Redis (or another broker)

```python
# config/settings.py
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "redis://localhost:6379/0"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Asia/Jakarta"
```

### 4. Start Workers

```bash
# Start Celery worker
celery -A config worker -l info

# Start Celery Beat (periodic tasks)
celery -A config beat -l info

# Or combined (development only)
celery -A config worker -B -l info
```

## Built-in Tasks

### One-off Tasks

| Task | Parameters | Description |
|------|-----------|-------------|
| `check_payment_status` | `order_id: str` | Check and update a single payment's status from Midtrans API |
| `process_charge_async` | `charge_kwargs: dict` | Create a payment charge asynchronously |
| `process_refund_async` | `order_id, amount, reason, direct` | Process a refund asynchronously |

### Periodic Tasks (Celery Beat)

| Task | Schedule | Description |
|------|----------|-------------|
| `check_pending_payments` | Every 5 minutes | Queues `check_payment_status` for all PENDING payments |
| `expire_stale_payments` | Every 10 minutes | Expires PENDING payments past their `expiry_time` |
| `check_overdue_invoices` | Every hour | Marks DRAFT/SENT invoices past `due_date` as OVERDUE |
| `sync_subscription_status` | Every 30 minutes | Syncs subscription statuses from Midtrans |

## Retry Configuration

Tasks that call the Midtrans API have automatic retry:

| Task | Max Retries | Backoff |
|------|------------|---------|
| `check_payment_status` | 3 | 60 seconds |
| `process_charge_async` | 3 | 30 seconds |
| `process_refund_async` | 3 | 30 seconds |

## Manual Task Invocation

### Check a Specific Payment

```python
from django_midtrans.tasks import check_payment_status

# Async (via Celery)
check_payment_status.delay("ORDER-001")

# Sync (direct call)
check_payment_status("ORDER-001")
```

### Async Charge

```python
from django_midtrans.tasks import process_charge_async

process_charge_async.delay({
    "payment_type": "bank_transfer",
    "gross_amount": 100000,
    "order_id": "ORDER-001",
    "bank": "bca",
    "customer_details": {
        "first_name": "John",
        "email": "john@example.com",
    },
})
```

### Async Refund

```python
from django_midtrans.tasks import process_refund_async

process_refund_async.delay(
    order_id="ORDER-001",
    amount=50000,
    reason="Customer request",
    direct=False,
)
```

## Celery Beat Schedule

If you want to override the default schedule, configure it in your settings:

```python
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "check-pending-payments": {
        "task": "django_midtrans.tasks.check_pending_payments",
        "schedule": 300.0,  # Every 5 minutes
    },
    "expire-stale-payments": {
        "task": "django_midtrans.tasks.expire_stale_payments",
        "schedule": 600.0,  # Every 10 minutes
    },
    "check-overdue-invoices": {
        "task": "django_midtrans.tasks.check_overdue_invoices",
        "schedule": crontab(minute=0),  # Every hour
    },
    "sync-subscription-status": {
        "task": "django_midtrans.tasks.sync_subscription_status",
        "schedule": 1800.0,  # Every 30 minutes
    },
}
```

## Without Celery

If you don't use Celery, you can still call tasks synchronously:

```python
from django_midtrans.tasks import check_payment_status

# Direct call (blocks)
check_payment_status("ORDER-001")
```

Or use Django management commands or cron jobs to run the periodic tasks:

```bash
# Via cron
*/5 * * * * cd /path/to/project && python manage.py shell -c "from django_midtrans.tasks import check_pending_payments; check_pending_payments()"
```
