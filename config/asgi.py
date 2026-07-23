"""
ASGI entrypoint.

HTTP is served by Django; WebSocket traffic is routed through Channels. The
AuthMiddlewareStack resolves the session cookie to scope["user"] on the
handshake (see ADR 0001 / chat.consumers), and AllowedHostsOriginValidator
rejects cross-origin socket attempts.
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Initialise Django before importing anything that touches models/routing.
django_asgi_app = get_asgi_application()

import chat.routing  # noqa: E402  (import after Django is initialised)

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(URLRouter(chat.routing.websocket_urlpatterns))
        ),
    }
)
