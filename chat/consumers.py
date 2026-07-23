"""
The chat WebSocket consumer.

Auth is the session cookie: `AuthMiddlewareStack` (wired in config/asgi.py) reads
it on the handshake and puts the user on `scope["user"]` — the exact reason
ADR 0001 kept auth cookie/session based. Browsers can't set an Authorization
header on a WebSocket, but they *do* send cookies, so this Just Works.

A "room" is a booking. Only its two participants may join; messages are
persisted and fanned out to the room's group over the Redis channel layer.
"""

import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.db.models import Q

from booking.models import Booking

from .models import ChatMessage

# Close codes (4000+ are application-defined).
CLOSE_UNAUTHENTICATED = 4401
CLOSE_FORBIDDEN = 4403


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get("user")
        self.booking_id = int(self.scope["url_route"]["kwargs"]["booking_id"])

        if self.user is None or self.user.is_anonymous:
            await self.close(code=CLOSE_UNAUTHENTICATED)
            return
        if not await self._is_participant():
            await self.close(code=CLOSE_FORBIDDEN)
            return

        self.group_name = f"chat_booking_{self.booking_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        try:
            body = (json.loads(text_data).get("message") or "").strip()
        except (TypeError, ValueError, AttributeError):
            return
        if not body:
            return

        message = await self._save_message(body)
        # Fan out to everyone in the room (including the sender, so the UI can
        # render from the server's authoritative copy — id + timestamp).
        await self.channel_layer.group_send(self.group_name, {
            "type": "chat.message",
            "id": message.id,
            "message": body,
            "sender_id": self.user.id,
            "sender": self.user.email,
            "created_at": message.created_at.isoformat(),
        })

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "id": event["id"],
            "message": event["message"],
            "sender_id": event["sender_id"],
            "sender": event["sender"],
            "created_at": event["created_at"],
        }))

    @database_sync_to_async
    def _is_participant(self):
        return Booking.objects.filter(
            Q(customer=self.user) | Q(provider__user=self.user),
            pk=self.booking_id,
        ).exists()

    @database_sync_to_async
    def _save_message(self, body):
        return ChatMessage.objects.create(
            booking_id=self.booking_id, sender=self.user, body=body,
        )
