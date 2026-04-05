# Celery Beat schedule configuration for django_midtrans.
# Merge this into your project's CELERY_BEAT_SCHEDULE setting.

MIDTRANS_CELERY_BEAT_SCHEDULE = {
    "midtrans-check-pending-payments": {
        "task": "django_midtrans.tasks.check_pending_payments",
        "schedule": 300.0,  # Every 5 minutes
        "options": {"queue": "midtrans"},
    },
    "midtrans-expire-stale-payments": {
        "task": "django_midtrans.tasks.expire_stale_payments",
        "schedule": 600.0,  # Every 10 minutes
        "options": {"queue": "midtrans"},
    },
    "midtrans-check-overdue-invoices": {
        "task": "django_midtrans.tasks.check_overdue_invoices",
        "schedule": 3600.0,  # Every hour
        "options": {"queue": "midtrans"},
    },
    "midtrans-sync-subscription-status": {
        "task": "django_midtrans.tasks.sync_subscription_status",
        "schedule": 1800.0,  # Every 30 minutes
        "options": {"queue": "midtrans"},
    },
}
