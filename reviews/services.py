"""
Rating aggregation — the single place ServiceProvider.rating_* is written.

`recompute_provider_rating` is the whole engine: lock the provider row, average
the reviews, write the two denormalised fields. Locking serialises concurrent
review changes for the same provider so the stored average can't be computed from
a half-applied set (same discipline as the booking slot lock, ADR 0002).
"""

from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction
from django.db.models import Avg, Count

from providers.models import ServiceProvider

from .models import Review

_TWO_PLACES = Decimal("0.01")


@transaction.atomic
def recompute_provider_rating(provider_id):
    ServiceProvider.objects.select_for_update().get(pk=provider_id)
    agg = Review.objects.filter(provider_id=provider_id).aggregate(
        avg=Avg("rating"), count=Count("id"),
    )
    avg = agg["avg"]
    rating_avg = (
        Decimal(str(avg)).quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)
        if avg is not None else Decimal("0.00")
    )
    ServiceProvider.objects.filter(pk=provider_id).update(
        rating_avg=rating_avg, rating_count=agg["count"] or 0,
    )
