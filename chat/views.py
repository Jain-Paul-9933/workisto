"""
Message history over plain HTTP — what a client loads when it opens a
conversation, before the live WebSocket takes over. Participant-scoped, same as
everything else booking-related.
"""

from django.db.models import Q
from rest_framework.generics import ListAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated

from booking.models import Booking

from .serializers import ChatMessageSerializer


class BookingMessagesView(ListAPIView):
    """GET /api/bookings/{id}/messages/ — this booking's chat history."""

    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        booking = get_object_or_404(
            Booking.objects.filter(
                Q(customer=self.request.user) | Q(provider__user=self.request.user),
            ),
            pk=self.kwargs["pk"],
        )
        return booking.messages.select_related("sender")
