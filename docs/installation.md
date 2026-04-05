# Installation

## Requirements

- Python 3.10+
- Django 4.2, 5.0, or 5.1
- Django REST Framework 3.14+

## Install from PyPI

```bash
pip install django-payment-midtrans
```

### Optional Extras

**Unfold Admin theme** (beautiful admin dashboard):

```bash
pip install django-payment-midtrans[unfold]
```

**Development tools** (testing, linting):

```bash
pip install django-payment-midtrans[dev]
```

**Documentation** (Sphinx):

```bash
pip install django-payment-midtrans[docs]
```

**All extras**:

```bash
pip install django-payment-midtrans[unfold,dev,docs]
```

## Install from Source

```bash
git clone https://github.com/rissets/django-payment-midtrans.git
cd django-payment-midtrans
pip install -e ".[unfold,dev]"
```

## Dependencies

The package automatically installs:

| Package | Version | Purpose |
|---------|---------|---------|
| Django | >= 4.2 | Web framework |
| djangorestframework | >= 3.14 | REST API |
| requests | >= 2.28 | HTTP client for Midtrans API |
| celery | >= 5.3 | Async task processing |
| django-celery-beat | >= 2.5 | Periodic task scheduling |

## Midtrans Account

You need a Midtrans account to use this package:

1. **Sandbox** (free, for development): [dashboard.sandbox.midtrans.com](https://dashboard.sandbox.midtrans.com)
2. **Production** (requires approval): [dashboard.midtrans.com](https://dashboard.midtrans.com)

After creating an account, get your credentials from:
**Settings → Access Keys** in the Midtrans Dashboard.

You will need:
- **Server Key** — Used for backend API calls
- **Client Key** — Used for frontend card tokenization (credit card payments)
- **Merchant ID** — Your merchant identifier
