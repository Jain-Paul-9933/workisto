"""Provider-facing read into the pricing engine's decisions."""

from rest_framework import generics

from accounts.permissions import IsProvider

from .models import PriceChange
from .serializers import PriceChangeSerializer


class OfferingPriceHistoryView(generics.ListAPIView):
    """GET /api/providers/me/offerings/{id}/price-history/ — why a price moved."""

    serializer_class = PriceChangeSerializer
    permission_classes = [IsProvider]

    def get_queryset(self):
        # Scoped to the caller's own offering — no peeking at others' pricing.
        return PriceChange.objects.filter(
            offering_id=self.kwargs["pk"],
            offering__provider__user=self.request.user,
        )
