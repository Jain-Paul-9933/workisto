"""
Chat is scoped to a booking — the customer and provider of a job talk about that
job. Messages are persisted (the WebSocket delivers them live; the DB is the
history a client loads on open).
"""

from django.conf import settings
from django.db import models

from booking.models import Booking


class ChatMessage(models.Model):
    booking = models.ForeignKey(
        Booking, on_delete=models.CASCADE, related_name="messages",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chat_messages",
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [models.Index(fields=["booking", "created_at"])]

    def __str__(self):
        return f"msg #{self.pk} on booking {self.booking_id}"
