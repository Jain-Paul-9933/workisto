"""
ASGI entrypoint.

Right now HTTP is the only protocol wired up. When we build chat, the
websocket branch gets a real URLRouter of consumers — the structure is already
here so that change is additive, not a rewrite.
"""

import os

from channels.routing import ProtocolTypeRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Initialise Django before importing anything that touches models/routing.
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        # "websocket": AuthMiddlewareStack(URLRouter(chat_websocket_urlpatterns)),
    }
)
