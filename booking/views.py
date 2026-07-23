"""
Booking endpoints. Bookings have two participants (customer and provider), so
every queryset is scoped to "bookings I'm a party to" — that both filters the
list and 404-guards detail/actions against outsiders. Which *action* each party
may take is enforced per-view (only the provider estimates; only the customer
confirms).
"""

from django.db.models import Q
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from providers.models import BookingType

from .models import Booking, BookingStatus
from .serializers import (
    BookingCreateSerializer,
    BookingSerializer,
    ConfirmSerializer,
    EstimateSerializer,
)
from .services import confirm_booking, create_consultation_request, create_instant_booking


def _participant_bookings(user):
    return Booking.objects.filter(Q(customer=user) | Q(provider__user=user))


class BookingListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        return BookingCreateSerializer if self.request.method == "POST" else BookingSerializer

    def get_queryset(self):
        return (
            _participant_bookings(self.request.user)
            .select_related("provider", "offering", "offering__category")
        )

    def create(self, request, *args, **kwargs):
        if request.user.role != User.Role.CUSTOMER:
            raise PermissionDenied("Only customers can create bookings.")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        offering = data["offering"]

        if offering.booking_type == BookingType.INSTANT:
            booking = create_instant_booking(
                customer=request.user, offering=offering, mode=data["mode"],
                start_at=data["start_at"], notes=data["notes"],
            )
        else:
            booking = create_consultation_request(
                customer=request.user, offering=offering, mode=data["mode"],
                notes=data["notes"],
            )
        return Response(BookingSerializer(booking).data, status=status.HTTP_201_CREATED)


class BookingDetailView(generics.RetrieveAPIView):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return _participant_bookings(self.request.user)


class BookingEstimateView(APIView):
    """POST /api/bookings/{id}/estimate/ — provider quotes a consultation."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        booking = get_object_or_404(_participant_bookings(request.user), pk=pk)
        if booking.provider.user_id != request.user.id:
            raise PermissionDenied("Only the provider can give an estimate.")
        if booking.status != BookingStatus.PENDING_ESTIMATE:
            raise ValidationError("An estimate can only be given while pending estimate.")

        serializer = EstimateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        booking.estimate_amount = serializer.validated_data["estimate_amount"]
        booking.status = BookingStatus.ESTIMATED
        booking.save(update_fields=["estimate_amount", "status", "updated_at"])
        return Response(BookingSerializer(booking).data)


class BookingConfirmView(APIView):
    """POST /api/bookings/{id}/confirm/ — customer accepts the estimate + slot."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        booking = get_object_or_404(_participant_bookings(request.user), pk=pk)
        if booking.customer_id != request.user.id:
            raise PermissionDenied("Only the customer can confirm this booking.")
        if booking.status != BookingStatus.ESTIMATED:
            raise ValidationError("Only an estimated booking can be confirmed.")

        serializer = ConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        booking = confirm_booking(booking, serializer.validated_data["start_at"])
        return Response(BookingSerializer(booking).data)


class BookingCancelView(APIView):
    """POST /api/bookings/{id}/cancel/ — either party calls it off."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        booking = get_object_or_404(_participant_bookings(request.user), pk=pk)
        if booking.status in (BookingStatus.CANCELLED, BookingStatus.COMPLETED):
            raise ValidationError("This booking can no longer be cancelled.")
        booking.status = BookingStatus.CANCELLED
        booking.save(update_fields=["status", "updated_at"])
        return Response(BookingSerializer(booking).data)
