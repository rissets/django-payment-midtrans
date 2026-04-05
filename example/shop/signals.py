"""
Signal handlers — react to Midtrans payment lifecycle events.

This shows how to use django_midtrans signals in your own app.
"""

import logging

from django.dispatch import receiver
from django.utils import timezone

from django_midtrans.signals import (
    payment_cancelled,
    payment_expired,
    payment_refunded,
    payment_settled,
)

logger = logging.getLogger("shop")


def _create_invoice_for_order(order, payment):
    """Create a MidtransInvoice + items for a paid order, if one doesn't exist yet."""
    from django_midtrans.constants import InvoiceStatus
    from django_midtrans.models import MidtransInvoice, MidtransInvoiceItem

    if MidtransInvoice.objects.filter(payment=payment).exists():
        return

    now = timezone.now()
    invoice_number = f"INV-{now.strftime('%Y%m%d%H%M%S')}-{str(order.id)[:8].upper()}"

    invoice = MidtransInvoice.objects.create(
        invoice_number=invoice_number,
        order_id=payment.order_id,
        status=InvoiceStatus.PAID,
        customer_name=order.user.get_full_name() or order.user.username,
        customer_email=order.user.email or f"{order.user.username}@example.com",
        user=order.user,
        total_amount=order.total,
        due_date=now.date(),
        paid_at=payment.settlement_time or now,
        payment=payment,
        notes=f"Auto-generated for Order {order.id}",
    )

    for item in order.items.select_related("product").all():
        MidtransInvoiceItem.objects.create(
            invoice=invoice,
            item_id=str(item.product.pk),
            description=item.product.name,
            quantity=item.quantity,
            price=item.price,
        )

    logger.info("Invoice %s created for order %s", invoice_number, order.id)


@receiver(payment_settled)
def handle_payment_settled(sender, payment, notification, **kwargs):
    """Mark the related order as paid when payment is settled."""
    from shop.models import Order

    try:
        order = Order.objects.get(midtrans_payment=payment)
        order.status = Order.Status.PAID
        order.save(update_fields=["status", "updated_at"])
        logger.info("Order %s marked as PAID (payment %s settled)", order.id, payment.order_id)
        _create_invoice_for_order(order, payment)
    except Order.DoesNotExist:
        logger.warning("No order found for payment %s", payment.order_id)


@receiver(payment_cancelled)
def handle_payment_cancelled(sender, payment, notification, **kwargs):
    """Mark the related order as cancelled."""
    from shop.models import Order

    try:
        order = Order.objects.get(midtrans_payment=payment)
        order.status = Order.Status.CANCELLED
        order.save(update_fields=["status", "updated_at"])
        logger.info("Order %s marked as CANCELLED (payment %s)", order.id, payment.order_id)
    except Order.DoesNotExist:
        pass


@receiver(payment_expired)
def handle_payment_expired(sender, payment, notification, **kwargs):
    """Mark the related order as cancelled when payment expires."""
    from shop.models import Order

    try:
        order = Order.objects.get(midtrans_payment=payment)
        order.status = Order.Status.CANCELLED
        order.save(update_fields=["status", "updated_at"])
        logger.info("Order %s cancelled — payment %s expired", order.id, payment.order_id)
    except Order.DoesNotExist:
        pass


@receiver(payment_refunded)
def handle_payment_refunded(sender, payment, notification, **kwargs):
    """Mark the related order as refunded."""
    from shop.models import Order

    try:
        order = Order.objects.get(midtrans_payment=payment)
        order.status = Order.Status.REFUNDED
        order.save(update_fields=["status", "updated_at"])
        logger.info("Order %s marked as REFUNDED (payment %s)", order.id, payment.order_id)
    except Order.DoesNotExist:
        pass
