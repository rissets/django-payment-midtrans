# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-12-01

### Added

- **Core Payment Processing**
  - Credit Card with 3DS authentication
  - Bank Transfer / Virtual Account (BCA, BNI, BRI, Permata, CIMB)
  - Mandiri Bill Payment (E-Channel)
  - E-Wallets: GoPay, ShopeePay, DANA
  - QRIS universal QR code payments
  - Convenience Store: Indomaret, Alfamart
  - Pay Later: Akulaku

- **Payment Operations**: status check, cancel, expire, refund (full/partial), capture

- **Invoice System**: creation, auto-numbering, status tracking, voiding

- **Subscription Management**: create, enable/disable/cancel, auto status sync

- **Webhook Handling**: SHA-512 signature verification, automatic status updates, duplicate detection

- **Django Signals**: 14 signals for payment, invoice, and subscription lifecycle events

- **Celery Tasks**: background status checks, stale payment expiry, overdue invoice detection, subscription sync

- **Django Admin**: rich admin with colored badges, filters, inline records, django-unfold support

- **REST API**: full CRUD via Django REST Framework

- **Example Application**: complete e-commerce demo

[1.0.0]: https://github.com/rissets/django-payment-midtrans/releases/tag/v1.0.0
