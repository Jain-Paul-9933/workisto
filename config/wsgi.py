"""WSGI entrypoint (kept for tooling / classic deploys; we serve via ASGI)."""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()
