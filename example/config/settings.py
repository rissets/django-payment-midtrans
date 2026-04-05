"""
Django settings for the example project.

Reads credentials from environment variables (via .env file).
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env from project root (one level above example/)
ENV_PATH = BASE_DIR.parent / ".env"
load_dotenv(ENV_PATH)

# Add parent directory to sys.path so django_midtrans package is importable
PACKAGE_DIR = str(BASE_DIR.parent)
if PACKAGE_DIR not in sys.path:
    sys.path.insert(0, PACKAGE_DIR)

# ─── Core ───────────────────────────────────────────────

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "insecure-dev-key-change-me")
DEBUG = os.environ.get("DJANGO_DEBUG", "True").lower() in ("true", "1", "yes")
ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "*").split(",")
    if h.strip()
]

# ─── Apps ───────────────────────────────────────────────

INSTALLED_APPS = [
    # Unfold must be before django.contrib.admin
    "unfold",
    "unfold.contrib.filters",

    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",

    # Third party
    "rest_framework",
    "django_celery_beat",

    # Our package
    "django_midtrans",

    # Example app
    "shop",
]

# ─── Middleware ──────────────────────────────────────────

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "shop.context_processors.cart_context",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ─── Database ───────────────────────────────────────────

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# ─── Auth ───────────────────────────────────────────────

AUTH_PASSWORD_VALIDATORS = []

# ─── Internationalization ───────────────────────────────

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Jakarta"
USE_I18N = True
USE_TZ = True

# ─── Static files ──────────────────────────────────────

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ─── Unfold Admin ──────────────────────────────────────

from django.urls import reverse_lazy  # noqa: E402
from django.utils.translation import gettext_lazy as _  # noqa: E402

UNFOLD = {
    "SITE_TITLE": "Midtrans Shop",
    "SITE_HEADER": "Midtrans Shop",
    "SITE_SUBHEADER": "Payment Gateway Demo",
    "SITE_URL": "/",
    "SITE_SYMBOL": "payments",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "ENVIRONMENT": "shop.dashboard.environment_callback",
    "DASHBOARD_CALLBACK": "shop.dashboard.dashboard_callback",
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": _("Navigation"),
                "separator": True,
                "collapsible": False,
                "items": [
                    {
                        "title": _("Dashboard"),
                        "icon": "dashboard",
                        "link": reverse_lazy("admin:index"),
                    },
                    {
                        "title": _("View Shop"),
                        "icon": "storefront",
                        "link": "/",
                    },
                ],
            },
            {
                "title": _("Shop"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Products"),
                        "icon": "inventory_2",
                        "link": reverse_lazy("admin:shop_product_changelist"),
                    },
                    {
                        "title": _("Orders"),
                        "icon": "receipt_long",
                        "link": reverse_lazy("admin:shop_order_changelist"),
                    },
                ],
            },
            {
                "title": _("Payments"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Payments"),
                        "icon": "payments",
                        "link": reverse_lazy("admin:django_midtrans_midtranspayment_changelist"),
                    },
                    {
                        "title": _("Notifications"),
                        "icon": "notifications",
                        "link": reverse_lazy("admin:django_midtrans_midtransnotification_changelist"),
                    },
                    {
                        "title": _("Invoices"),
                        "icon": "description",
                        "link": reverse_lazy("admin:django_midtrans_midtransinvoice_changelist"),
                    },
                    {
                        "title": _("Subscriptions"),
                        "icon": "autorenew",
                        "link": reverse_lazy("admin:django_midtrans_midtranssubscription_changelist"),
                    },
                    {
                        "title": _("Refunds"),
                        "icon": "undo",
                        "link": reverse_lazy("admin:django_midtrans_midtransrefund_changelist"),
                    },
                ],
            },
            {
                "title": _("System"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Users"),
                        "icon": "people",
                        "link": reverse_lazy("admin:auth_user_changelist"),
                    },
                    {
                        "title": _("Periodic Tasks"),
                        "icon": "schedule",
                        "link": reverse_lazy("admin:django_celery_beat_periodictask_changelist"),
                    },
                ],
            },
        ],
    },
}

# ─── REST Framework ────────────────────────────────────

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

# ─── Midtrans Configuration (from .env) ────────────────

MIDTRANS = {
    "SERVER_KEY": os.environ.get("MIDTRANS_SERVER_KEY", ""),
    "CLIENT_KEY": os.environ.get("MIDTRANS_CLIENT_KEY", ""),
    "MERCHANT_ID": os.environ.get("MIDTRANS_MERCHANT_ID", ""),
    "IS_PRODUCTION": os.environ.get("MIDTRANS_IS_PRODUCTION", "False").lower() in ("true", "1"),
    "NOTIFICATION_URL": os.environ.get("MIDTRANS_NOTIFICATION_URL", ""),
    "ENABLED_PAYMENT_METHODS": [
        "credit_card",
        "gopay",
        "shopeepay",
        "qris",
        "bank_transfer",
        "echannel",
        "cstore",
    ],
}

# ─── Celery ─────────────────────────────────────────────

CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "memory://")
CELERY_RESULT_BACKEND = "django-db"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

# Register Midtrans beat schedules
from django_midtrans.schedules import MIDTRANS_CELERY_BEAT_SCHEDULE  # noqa: E402

CELERY_BEAT_SCHEDULE = {
    **MIDTRANS_CELERY_BEAT_SCHEDULE,
}

# ─── Logging ────────────────────────────────────────────

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django_midtrans": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "shop": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}
