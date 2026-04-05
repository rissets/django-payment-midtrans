import logging

from celery import shared_task
from django.utils import timezone

from django_midtrans.app_settings import midtrans_settings
from django_midtrans.constants import InvoiceStatus, TransactionStatus
from django_midtrans.exceptions import MidtransError

logger = logging.getLogger("django_midtrans")


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(MidtransError,),
    retry_backoff=True,
)
def check_payment_status(self, order_id):
    """Check and update the status of a single payment from Midtrans."""
    from django_midtrans.models import MidtransPayment
    from django_midtrans.services import PaymentService

    try:
        payment = MidtransPayment.objects.get(order_id=order_id)
    except MidtransPayment.DoesNotExist:
        logger.error("Payment not found: %s", order_id)
        return {"error": f"Payment {order_id} not found"}

    if payment.is_final:
        return {"order_id": order_id, "status": payment.transaction_status, "skipped": True}

    service = PaymentService()
    response = service.get_status(payment)

    return {
        "order_id": order_id,
        "status": payment.transaction_status,
        "midtrans_status": response.get("transaction_status"),
    }


@shared_task(bind=True, max_retries=1)
def check_pending_payments(self):
    """
    Periodic task: Check status of all pending payments.
    Designed to be run by Celery Beat.
    """
    from django_midtrans.models import MidtransPayment
    from django_midtrans.services import PaymentService

    pending = MidtransPayment.objects.filter(
        transaction_status=TransactionStatus.PENDING,
    ).values_list("order_id", flat=True)

    count = 0
    for order_id in pending:
        check_payment_status.delay(order_id)
        count += 1

    logger.info("Queued status checks for %d pending payments", count)
    return {"queued": count}


@shared_task(bind=True, max_retries=1)
def expire_stale_payments(self):
    """
    Periodic task: Expire payments that have passed their expiry time.
    """
    from django_midtrans.models import MidtransPayment
    from django_midtrans.services import PaymentService

    now = timezone.now()
    stale = MidtransPayment.objects.filter(
        transaction_status=TransactionStatus.PENDING,
        expiry_time__lt=now,
    )

    service = PaymentService()
    count = 0
    for payment in stale:
        try:
            service.expire_payment(payment)
            count += 1
        except MidtransError as e:
            logger.warning("Failed to expire payment %s: %s", payment.order_id, str(e))

    logger.info("Expired %d stale payments", count)
    return {"expired": count}


@shared_task(bind=True, max_retries=1)
def check_overdue_invoices(self):
    """
    Periodic task: Mark overdue invoices.
    """
    from django_midtrans.models import MidtransInvoice

    today = timezone.now().date()
    updated = MidtransInvoice.objects.filter(
        status__in=[InvoiceStatus.DRAFT, InvoiceStatus.SENT],
        due_date__lt=today,
    ).update(status=InvoiceStatus.OVERDUE)

    logger.info("Marked %d invoices as overdue", updated)
    return {"overdue": updated}


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    autoretry_for=(MidtransError,),
    retry_backoff=True,
)
def process_charge_async(self, charge_kwargs):
    """
    Async payment charge processing.
    Useful for non-blocking charge creation.
    """
    from django_midtrans.services import PaymentService

    service = PaymentService()
    payment, response = service.create_charge(**charge_kwargs)
    return {
        "order_id": payment.order_id,
        "transaction_status": payment.transaction_status,
        "payment_id": str(payment.id),
    }


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    autoretry_for=(MidtransError,),
    retry_backoff=True,
)
def process_refund_async(self, order_id, amount, reason="", direct=False):
    """Async refund processing."""
    from django_midtrans.services import PaymentService

    service = PaymentService()
    payment, refund, response = service.refund_payment(
        order_id, amount=amount, reason=reason, direct=direct,
    )
    return {
        "order_id": payment.order_id,
        "refund_key": refund.refund_key,
        "refund_amount": str(refund.amount),
    }


@shared_task(bind=True, max_retries=1)
def sync_subscription_status(self):
    """
    Periodic task: Sync subscription statuses from Midtrans.
    """
    from django_midtrans.models import MidtransSubscription
    from django_midtrans.services import SubscriptionService

    active_subs = MidtransSubscription.objects.filter(
        status__in=["active", "inactive"],
    )

    service = SubscriptionService()
    updated = 0
    for sub in active_subs:
        try:
            response = service.get_subscription_status(sub)
            new_status = response.get("status", sub.status)
            if new_status != sub.status:
                sub.status = new_status
                sub.save(update_fields=["status", "updated_at"])
                updated += 1
        except MidtransError as e:
            logger.warning("Failed to sync subscription %s: %s", sub.midtrans_subscription_id, str(e))

    logger.info("Synced %d subscription statuses", updated)
    return {"synced": updated}
