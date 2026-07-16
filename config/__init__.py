# Make sure the Celery app is loaded when Django starts, so the @shared_task
# decorator (used in later increments) can find it.
from .celery import app as celery_app

__all__ = ("celery_app",)
