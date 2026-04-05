from django.conf import settings

MIDTRANS_DEFAULTS = {
    "SERVER_KEY": "",
    "CLIENT_KEY": "",
    "MERCHANT_ID": "",
    "IS_PRODUCTION": False,
    "NOTIFICATION_URL": "",
    "PAYMENT_EXPIRY_MINUTES": 1440,
    "AUTO_CHECK_STATUS_INTERVAL": 300,
    "ENABLED_PAYMENT_METHODS": [
        "credit_card",
        "gopay",
        "shopeepay",
        "qris",
        "ovo",
        "dana",
        "bank_transfer",
        "echannel",
        "cstore",
    ],
    "CALLBACK_URL_GOPAY": "",
    "CALLBACK_URL_SHOPEEPAY": "",
    "DEFAULT_CURRENCY": "IDR",
    "CUSTOM_EXPIRY_UNIT": "minute",
    "INVOICE_AUTO_NUMBER": True,
    "INVOICE_PREFIX": "INV",
}


class MidtransSettings:
    def __getattr__(self, name):
        if name not in MIDTRANS_DEFAULTS:
            raise AttributeError(f"Invalid Midtrans setting: {name}")
        user_settings = getattr(settings, "MIDTRANS", {})
        return user_settings.get(name, MIDTRANS_DEFAULTS[name])

    @property
    def BASE_URL(self):
        if self.IS_PRODUCTION:
            return "https://api.midtrans.com"
        return "https://api.sandbox.midtrans.com"

    @property
    def DASHBOARD_URL(self):
        if self.IS_PRODUCTION:
            return "https://dashboard.midtrans.com"
        return "https://dashboard.sandbox.midtrans.com"


midtrans_settings = MidtransSettings()
