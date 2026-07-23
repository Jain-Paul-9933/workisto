from django.apps import AppConfig


class ReviewsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "reviews"

    def ready(self):
        # Wire the signals that keep ServiceProvider.rating_* in sync.
        from . import signals  # noqa: F401
