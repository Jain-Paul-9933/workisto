from django.apps import AppConfig


class PricingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "pricing"

    def ready(self):
        # Subscribe to review changes so ratings drive prices.
        from . import signals  # noqa: F401
