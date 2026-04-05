import django.dispatch

# Payment lifecycle signals
payment_received = django.dispatch.Signal()      # Pending payment created
payment_settled = django.dispatch.Signal()        # Payment successfully settled/captured
payment_denied = django.dispatch.Signal()         # Payment denied
payment_cancelled = django.dispatch.Signal()      # Payment cancelled
payment_expired = django.dispatch.Signal()        # Payment expired
payment_refunded = django.dispatch.Signal()       # Payment refunded (full or partial)
payment_failed = django.dispatch.Signal()         # Payment failed

# Invoice signals
invoice_created = django.dispatch.Signal()
invoice_paid = django.dispatch.Signal()
invoice_voided = django.dispatch.Signal()

# Subscription signals
subscription_created = django.dispatch.Signal()
subscription_charged = django.dispatch.Signal()
subscription_disabled = django.dispatch.Signal()
subscription_cancelled = django.dispatch.Signal()
