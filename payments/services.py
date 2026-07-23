"""
Payment orchestration: what to charge, and turning that into a gateway intent.

Amounts are derived server-side from the booking — the client never names its
own price. The consultation fee, if it was paid, is credited against the final
balance (as promised on the offering).
"""

from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.db import transaction
from rest_framework.exceptions import ValidationError

from .gateway import get_gateway
from .models import Payment, PaymentKind, PaymentStatus

ADVANCE_FRACTION = Decimal("0.30")   # deposit taken up front on a confirmed job
_CENTS = Decimal("0.01")


def _q(amount):
    return amount.quantize(_CENTS, rounding=ROUND_HALF_UP)


def _consultation_paid(booking):
    return Payment.objects.filter(
        booking=booking, kind=PaymentKind.CONSULTATION,
        status=PaymentStatus.SUCCEEDED,
    ).exists()


def amount_for(booking, kind):
    """Server-authoritative amount for a payment of `kind` on `booking`."""
    if kind == PaymentKind.CONSULTATION:
        return _q(booking.consultation_fee)

    total = booking.price or Decimal("0.00")
    advance = _q(total * ADVANCE_FRACTION)
    if kind == PaymentKind.ADVANCE:
        return advance
    if kind == PaymentKind.FINAL:
        credit = booking.consultation_fee if _consultation_paid(booking) else Decimal("0.00")
        return max(Decimal("0.00"), _q(total - advance - credit))
    raise ValidationError({"kind": "Unknown payment kind."})


def _to_minor_units(amount):
    # Stripe wants the smallest currency unit (paise for INR).
    return int((amount * 100).to_integral_value(rounding=ROUND_HALF_UP))


@transaction.atomic
def create_payment(booking, kind):
    amount = amount_for(booking, kind)
    if amount <= 0:
        raise ValidationError("Nothing to pay for this.")
    if Payment.objects.filter(
        booking=booking, kind=kind, status=PaymentStatus.SUCCEEDED,
    ).exists():
        raise ValidationError(f"The {kind.lower()} payment is already settled.")

    payment = Payment.objects.create(
        booking=booking, kind=kind, amount=amount,
        currency=settings.PAYMENT_CURRENCY,
    )
    intent = get_gateway().create_intent(
        amount=_to_minor_units(amount),
        currency=payment.currency,
        metadata={"payment_id": payment.id, "booking_id": booking.id},
    )
    payment.external_id = intent.id
    payment.client_secret = intent.client_secret
    payment.save(update_fields=["external_id", "client_secret", "updated_at"])
    return payment


def apply_webhook_event(event):
    """Idempotently reconcile our record with what the gateway reports."""
    if event.type == "payment_intent.succeeded":
        Payment.objects.filter(external_id=event.intent_id).exclude(
            status=PaymentStatus.SUCCEEDED,
        ).update(status=PaymentStatus.SUCCEEDED)
    elif event.type == "payment_intent.payment_failed":
        Payment.objects.filter(
            external_id=event.intent_id, status=PaymentStatus.PENDING,
        ).update(status=PaymentStatus.FAILED)
    # Any other event type is acknowledged and ignored.
