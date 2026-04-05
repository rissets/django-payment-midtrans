from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DjangoMidtransConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_midtrans"
    verbose_name = _("Midtrans Payment")

    def ready(self):
        import django_midtrans.signals  # noqa: F401
