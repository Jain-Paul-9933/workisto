"""
Review endpoints. Writing is owner-scoped (you create reviews for your own
completed bookings, and can only touch your own afterwards); reading a provider's
reviews is public, since that's what a customer weighs before booking.
"""

from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated

from .models import Review
from .serializers import (
    ReviewCreateSerializer,
    ReviewSerializer,
    ReviewUpdateSerializer,
)


class ReviewCreateView(generics.CreateAPIView):
    serializer_class = ReviewCreateSerializer
    permission_classes = [IsAuthenticated]  # booking-ownership enforced in serializer


class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Scoped to the author → others can't read/edit/delete via this route.
        return Review.objects.filter(customer=self.request.user)

    def get_serializer_class(self):
        return ReviewSerializer if self.request.method == "GET" else ReviewUpdateSerializer


class ProviderReviewListView(generics.ListAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return (
            Review.objects
            .filter(provider_id=self.kwargs["pk"])
            .select_related("customer")
        )
