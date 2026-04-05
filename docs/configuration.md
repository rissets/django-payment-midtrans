# Configuration

All settings are placed inside the `MIDTRANS` dictionary in your Django `settings.py`.

## Full Reference

```python
# settings.py
MIDTRANS = {
    # ── Credentials (required) ──────────────────────────────────
    "SERVER_KEY": "",              # Midtrans Server Key
    "CLIENT_KEY": "",              # Midtrans Client Key (for frontend)
    "MERCHANT_ID": "",             # Midtrans Merchant ID

    # ── Environment ─────────────────────────────────────────────
    "IS_PRODUCTION": False,        # True = production, False = sandbox

    # ── Webhook ─────────────────────────────────────────────────
    "NOTIFICATION_URL": "",        # Public URL for Midtrans webhooks

    # ── Payment Defaults ────────────────────────────────────────
    "PAYMENT_EXPIRY_MINUTES": 1440,          # 24 hours
    "AUTO_CHECK_STATUS_INTERVAL": 300,       # 5 minutes (Celery)
    "DEFAULT_CURRENCY": "IDR",

    # ── Payment Methods ─────────────────────────────────────────
    "ENABLED_PAYMENT_METHODS": [
        "credit_card",
        "gopay",
        "shopeepay",
        "dana",
        "qris",
        "bank_transfer",
        "echannel",
        "cstore",
        "akulaku",
        "kredivo",
    ],
}
```

## Settings Detail

### Credentials

| Setting | Type | Required | Description |
|---------|------|----------|-------------|
| `SERVER_KEY` | `str` | **Yes** | Your Midtrans Server Key. Used for all backend API calls. Found in Midtrans Dashboard → Settings → Access Keys. |
| `CLIENT_KEY` | `str` | For CC | Your Midtrans Client Key. Required for frontend credit card tokenization. |
| `MERCHANT_ID` | `str` | Optional | Your Midtrans Merchant ID. Used for some API calls. |

### Environment

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `IS_PRODUCTION` | `bool` | `False` | Controls which Midtrans API server is used. `False` = sandbox (`api.sandbox.midtrans.com`), `True` = production (`api.midtrans.com`). |

### Webhook

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `NOTIFICATION_URL` | `str` | `""` | The public URL where Midtrans sends payment notifications. Must be accessible from the internet. For local development, use ngrok or cloudflared. |

### Payment Defaults

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `PAYMENT_EXPIRY_MINUTES` | `int` | `1440` | How long before unpaid payments expire (in minutes). 1440 = 24 hours. |
| `AUTO_CHECK_STATUS_INTERVAL` | `int` | `300` | Interval in seconds for the Celery task that checks pending payment statuses. |
| `DEFAULT_CURRENCY` | `str` | `"IDR"` | Default currency for payments. |

### Payment Methods

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `ENABLED_PAYMENT_METHODS` | `list[str]` | All methods | List of payment type strings to enable. If not set, all methods are available. |

**Valid payment type strings:**

| Value | Payment Method |
|-------|---------------|
| `credit_card` | Credit/Debit Card (3DS) |
| `gopay` | GoPay e-wallet |
| `shopeepay` | ShopeePay e-wallet |
| `dana` | DANA e-wallet |
| `qris` | QRIS (universal QR) |
| `bank_transfer` | Virtual Account (BCA, BNI, BRI, Permata, CIMB) |
| `echannel` | Mandiri Bill Payment |
| `cstore` | Convenience Store (Indomaret, Alfamart) |
| `akulaku` | Akulaku PayLater |
| `kredivo` | Kredivo PayLater |

## Environment Variables

We recommend using environment variables for sensitive credentials:

```bash
# .env
MIDTRANS_SERVER_KEY=SB-Mid-server-xxxxxxxxxxxxxxxxxxxx
MIDTRANS_CLIENT_KEY=SB-Mid-client-xxxxxxxxxxxx
MIDTRANS_MERCHANT_ID=G000000000
MIDTRANS_IS_PRODUCTION=False
MIDTRANS_NOTIFICATION_URL=https://your-domain.ngrok-free.app/api/midtrans/notification/
```

Then in `settings.py`:

```python
import os

MIDTRANS = {
    "SERVER_KEY": os.environ.get("MIDTRANS_SERVER_KEY", ""),
    "CLIENT_KEY": os.environ.get("MIDTRANS_CLIENT_KEY", ""),
    "MERCHANT_ID": os.environ.get("MIDTRANS_MERCHANT_ID", ""),
    "IS_PRODUCTION": os.environ.get("MIDTRANS_IS_PRODUCTION", "False").lower() == "true",
    "NOTIFICATION_URL": os.environ.get("MIDTRANS_NOTIFICATION_URL", ""),
}
```

## Accessing Settings at Runtime

```python
from django_midtrans import midtrans_settings

# Read any setting
server_key = midtrans_settings.SERVER_KEY
is_prod = midtrans_settings.IS_PRODUCTION
base_url = midtrans_settings.BASE_URL        # Computed: sandbox or production URL
dashboard_url = midtrans_settings.DASHBOARD_URL  # Computed: dashboard URL
```

## API Base URLs

The `BASE_URL` is computed automatically from `IS_PRODUCTION`:

| Environment | API Base URL |
|-------------|-------------|
| Sandbox | `https://api.sandbox.midtrans.com` |
| Production | `https://api.midtrans.com` |
