import logging

from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from django_midtrans.client import MidtransClient
from django_midtrans.constants import NotificationStatus, TransactionStatus
from django_midtrans.models import MidtransNotification, MidtransPayment
from django_midtrans.signals import (
    payment_cancelled,
    payment_denied,
    payment_expired,
    payment_failed,
    payment_received,
    payment_refunded,
    payment_settled,
)

logger = logging.getLogger("django_midtrans")


class NotificationHandler:
    """
    Processes Midtrans webhook notifications with signature verification,
    idempotent processing, and Django signal dispatch.
    """

    @transaction.atomic
    def handle(self, payload):
        order_id = payload.get("order_id", "")
        transaction_status = payload.get("transaction_status", "")
        fraud_status = payload.get("fraud_status", "")
        payment_type = payload.get("payment_type", "")
        status_code = payload.get("status_code", "")
        gross_amount = payload.get("gross_amount", "")
        signature_key = payload.get("signature_key", "")

        # Reject empty/test pings with no meaningful data
        if not order_id or not signature_key:
            notification = MidtransNotification(
                order_id=order_id or "",
                transaction_status=transaction_status,
                payment_type=payment_type,
                status_code=status_code,
                gross_amount=gross_amount,
                raw_payload=payload,
                status=NotificationStatus.INVALID_SIGNATURE,
                error_message="Missing order_id or signature_key (test ping?)",
            )
            notification.save()
            logger.info("Ignored notification with missing order_id or signature_key")
            return notification

        # Create notification record
        notification = MidtransNotification(
            order_id=order_id,
            transaction_id=payload.get("transaction_id", ""),
            transaction_status=transaction_status,
            fraud_status=fraud_status,
            payment_type=payment_type,
            status_code=status_code,
            gross_amount=gross_amount,
            signature_key=signature_key,
            raw_payload=payload,
            status=NotificationStatus.RECEIVED,
        )

        # Verify signature
        if not MidtransClient.verify_signature(order_id, status_code, gross_amount, signature_key):
            notification.status = NotificationStatus.INVALID_SIGNATURE
            notification.error_message = "Signature verification failed"
            notification.save()
            logger.warning("Invalid signature for order %s", order_id)
            return notification

        # Lookup payment
        try:
            payment = MidtransPayment.objects.select_for_update().get(order_id=order_id)
            notification.payment = payment
        except MidtransPayment.DoesNotExist:
            notification.status = NotificationStatus.FAILED
            notification.error_message = f"Payment with order_id '{order_id}' not found"
            notification.save()
            logger.error("Payment not found for order %s", order_id)
            return notification

        # Idempotency check — skip if payment already in final state and same status
        if payment.is_final and payment.transaction_status == transaction_status:
            notification.status = NotificationStatus.DUPLICATE
            notification.save()
            logger.info("Duplicate notification for order %s (status: %s)", order_id, transaction_status)
            return notification

        # Update payment
        try:
            self._update_payment(payment, payload)
            notification.status = NotificationStatus.PROCESSED
            notification.save()
            self._dispatch_signal(payment, notification, payload)
            logger.info("Processed notification for order %s -> %s", order_id, transaction_status)
        except Exception as e:
            notification.status = NotificationStatus.FAILED
            notification.error_message = str(e)
            notification.save()
            logger.exception("Failed to process notification for order %s", order_id)

        return notification

    def _update_payment(self, payment, payload):
        transaction_status = payload.get("transaction_status", "")
        fraud_status = payload.get("fraud_status", "")

        payment.transaction_status = transaction_status
        payment.fraud_status = fraud_status
        payment.status_code = payload.get("status_code", "")
        payment.status_message = payload.get("status_message", "")
        payment.transaction_id = payload.get("transaction_id", payment.transaction_id)

        if settlement_time := payload.get("settlement_time"):
            dt = parse_datetime(settlement_time.replace(" ", "T"))
            if dt and timezone.is_naive(dt):
                dt = timezone.make_aware(dt)
            payment.settlement_time = dt

        update_fields = [
            "transaction_status", "fraud_status", "status_code",
            "status_message", "transaction_id", "settlement_time", "updated_at",
        ]
        payment.save(update_fields=update_fields)

    def _dispatch_signal(self, payment, notification, payload):
        signal_map = {
            TransactionStatus.SETTLEMENT: payment_settled,
            TransactionStatus.CAPTURE: payment_settled,
            TransactionStatus.PENDING: payment_received,
            TransactionStatus.DENY: payment_denied,
            TransactionStatus.CANCEL: payment_cancelled,
            TransactionStatus.EXPIRE: payment_expired,
            TransactionStatus.REFUND: payment_refunded,
            TransactionStatus.PARTIAL_REFUND: payment_refunded,
            TransactionStatus.FAILURE: payment_failed,
        }

        status = payload.get("transaction_status", "")

        # Special case for capture with fraud_status
        if status == TransactionStatus.CAPTURE:
            fraud = payload.get("fraud_status", "")
            if fraud == "challenge":
                payment_received.send(
                    sender=self.__class__, payment=payment,
                    notification=notification, payload=payload,
                )
                return
            elif fraud == "deny":
                payment_denied.send(
                    sender=self.__class__, payment=payment,
                    notification=notification, payload=payload,
                )
                return

        signal = signal_map.get(status)
        if signal:
            signal.send(
                sender=self.__class__, payment=payment,
                notification=notification, payload=payload,
            )
