# Changelog

## 1.0.0 (2024-12-01)

### Added

- **Core Payment Processing**
  - Credit Card with 3DS authentication
  - Bank Transfer / Virtual Account (BCA, BNI, BRI, Permata, CIMB)
  - Mandiri Bill Payment (E-Channel)
  - E-Wallets: GoPay, ShopeePay, DANA
  - QRIS universal QR code payments
  - Convenience Store: Indomaret, Alfamart
  - Pay Later: Akulaku

- **Payment Operations**
  - Payment status checking
  - Payment cancellation and expiry
  - Full and partial refunds (online and direct)
  - Pre-authorization capture

- **Invoice System**
  - Invoice creation with auto-numbering
  - Invoice status tracking
  - Invoice voiding

- **Subscription Management**
  - Create recurring subscriptions (Credit Card, GoPay)
  - Enable/disable/cancel subscriptions
  - Automatic status sync

- **Webhook Handling**
  - SHA-512 signature verification
  - Automatic payment status updates
  - Duplicate detection
  - Notification audit trail

- **Django Signals**
  - 14 signals for payment, invoice, and subscription events
  - Easy integration with business logic

- **Celery Tasks**
  - Background payment status checking
  - Automatic expiry of stale payments
  - Overdue invoice detection
  - Subscription status sync

- **Django Admin**
  - Rich admin interface for all models
  - Colored status badges
  - Inline items and refund records
  - django-unfold theme support with detail actions

- **REST API**
  - Full CRUD API via Django REST Framework
  - Charge, status check, cancel, expire, refund, capture endpoints
  - Invoice and subscription management endpoints

- **Example Application**
  - Complete e-commerce demo with shopping cart
  - All payment methods demonstrated
  - Unfold admin dashboard
  - Signal-based order status sync
