"""
Booking flow logic, kept out of the views so the slot-safety guarantee lives in
one auditable place.

## The double-booking problem

Two customers race for the same provider's 3pm slot. The naive "check then
insert" loses: both transactions run the overlap query, both see zero conflicts,
both insert. `SELECT ... FOR UPDATE` on the *existing* bookings doesn't fix it
either — there are no rows yet to lock (a phantom).

## The fix

We lock the **provider row** before checking. Every slot reservation for a given
provider must first `SELECT ... FOR UPDATE` that one row, so the racers are
serialized: the first locks it, checks, inserts, commits, releases; the second
then acquires the lock, sees the fresh booking, and is rejected. Contention is
per-provider and a provider books one job at a time, so this is cheap.

(A Postgres `EXCLUDE USING gist` constraint over `(provider, tstzrange)` would
enforce this at the storage layer too — considered, deferred; see the increment
notes. The app-level lock also gives us a clean 409 instead of an IntegrityError.)
"""

from datetime import timedelta

from django.db import transaction
from rest_framework.exceptions import APIException

from providers.models import ServiceProvider

from .models import BLOCKING_STATUSES, Booking, BookingStatus


class SlotUnavailable(APIException):
    status_code = 409
    default_detail = "That time slot is no longer available."
    default_code = "slot_unavailable"


def _lock_provider_and_check(provider_id, start_at, end_at, *, exclude_pk=None):
    """Serialize on the provider row, then reject if the window overlaps an
    existing blocking booking. MUST run inside a transaction."""
    # The lock is the whole point — hold it for the rest of the transaction.
    ServiceProvider.objects.select_for_update().get(pk=provider_id)

    overlap = Booking.objects.filter(
        provider_id=provider_id,
        status__in=BLOCKING_STATUSES,
        start_at__lt=end_at,   # existing starts before ours ends ...
        end_at__gt=start_at,   # ... and ends after ours starts  → they overlap
    )
    if exclude_pk is not None:
        overlap = overlap.exclude(pk=exclude_pk)
    if overlap.exists():
        raise SlotUnavailable()


@transaction.atomic
def create_instant_booking(*, customer, offering, mode, start_at, notes=""):
    """Instant offering → straight to CONFIRMED, slot guarded."""
    end_at = start_at + timedelta(minutes=offering.duration_minutes)
    _lock_provider_and_check(offering.provider_id, start_at, end_at)
    return Booking.objects.create(
        customer=customer,
        provider=offering.provider,
        offering=offering,
        mode=mode,
        status=BookingStatus.CONFIRMED,
        start_at=start_at,
        end_at=end_at,
        price=offering.current_price,
        notes=notes,
    )


def create_consultation_request(*, customer, offering, mode, notes=""):
    """Consultation-required offering → a request awaiting the provider's quote.
    No slot is held yet, so no locking is needed."""
    return Booking.objects.create(
        customer=customer,
        provider=offering.provider,
        offering=offering,
        mode=mode,
        status=BookingStatus.PENDING_ESTIMATE,
        consultation_fee=offering.consultation_fee,
        notes=notes,
    )


@transaction.atomic
def confirm_booking(booking, start_at):
    """Customer accepts the estimate and picks a slot → CONFIRMED, slot guarded."""
    end_at = start_at + timedelta(minutes=booking.offering.duration_minutes)
    _lock_provider_and_check(booking.provider_id, start_at, end_at, exclude_pk=booking.pk)
    booking.start_at = start_at
    booking.end_at = end_at
    booking.status = BookingStatus.CONFIRMED
    booking.price = booking.estimate_amount
    booking.save(update_fields=["start_at", "end_at", "status", "price", "updated_at"])
    return booking
