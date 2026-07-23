"""
Payment endpoints.

- Creating a payment and listing a booking's payments are booking-scoped: only a
  party to the booking can see them, and only the customer can pay.
- The webhook is the one open endpoint — no session, no CSRF — because Stripe
  calls it server-to-server. Its trust comes from the signature the gateway
  verifies, not from auth.
"""

from django.db.models import Q
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import ListAPIView, get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from booking.models import Booking

from .gateway import WebhookError, get_gateway
from .models import Payment
from .serializers import PaymentSerializer, PayRequestSerializer
from .services import apply_webhook_event, create_payment


def _participant_bookings(user):
    return Booking.objects.filter(Q(customer=user) | Q(provider__user=user))


class BookingPayView(APIView):
    """POST /api/bookings/{id}/pay/ — customer starts a payment for the booking."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        booking = get_object_or_404(_participant_bookings(request.user), pk=pk)
        if booking.customer_id != request.user.id:
            raise PermissionDenied("Only the customer can pay for this booking.")

        serializer = PayRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment = create_payment(booking, serializer.validated_data["kind"])
        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)


class BookingPaymentsView(ListAPIView):
    """GET /api/bookings/{id}/payments/ — either party sees the money trail."""

    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        booking = get_object_or_404(
            _participant_bookings(self.request.user), pk=self.kwargs["pk"],
        )
        return booking.payments.all()


class StripeWebhookView(APIView):
    """POST /api/payments/webhook/ — Stripe → us. No auth; the signature is."""

    authentication_classes = []   # no SessionAuth ⇒ no CSRF enforcement
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            # request.body (raw bytes) — we never touch request.data, so the
            # stream stays intact for signature verification.
            event = get_gateway().verify_webhook(
                request.body, request.headers.get("Stripe-Signature", ""),
            )
        except WebhookError:
            return Response({"detail": "Invalid signature."},
                            status=status.HTTP_400_BAD_REQUEST)

        apply_webhook_event(event)
        return Response(status=status.HTTP_200_OK)
