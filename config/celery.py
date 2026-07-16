"""Celery application. Tasks live in each app's tasks.py and use @shared_task."""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("workisto")

# Pull all CELERY_* settings straight from Django settings.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks.py in every installed app.
app.autodiscover_tasks()
