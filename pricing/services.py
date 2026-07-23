"""
The dynamic-pricing engine.

A provider's reputation moves their prices: `current_price = base_price ×
multiplier(rating)`. The multiplier is deliberately conservative and bounded —
a marketplace that swings prices wildly on one review loses trust.

Rules:
- Below `MIN_REVIEWS`, price sits at base (×1.00). One 5★ shouldn't spike a
  price, and a brand-new provider isn't penalised for having no reviews.
- Above it, price scales linearly around a neutral rating and is clamped, so a
  great provider earns a modest premium and a poor one auto-discounts, both
  within sane rails.

The engine is idempotent (it derives price purely from base + current rating),
and it locks the provider row while it runs so overlapping recomputes for the
same provider serialise on a stable rating.
"""

from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction

from providers.models import ServiceProvider

from .models import PriceChange

# --- Tunables (could move to settings; kept here, close to the logic) --------
MIN_REVIEWS = 3
NEUTRAL_RATING = Decimal("3.0")
SENSITIVITY = Decimal("0.10")       # price move per rating point away from neutral
MIN_MULTIPLIER = Decimal("0.85")
MAX_MULTIPLIER = Decimal("1.25")

_CENTS = Decimal("0.01")


def multiplier_for(rating_avg, rating_count):
    """The price multiplier for a given reputation. Pure; easy to unit-test."""
    if rating_count < MIN_REVIEWS:
        return Decimal("1.00")
    raw = Decimal("1.00") + (rating_avg - NEUTRAL_RATING) * SENSITIVITY
    clamped = max(MIN_MULTIPLIER, min(MAX_MULTIPLIER, raw))
    return clamped.quantize(_CENTS, rounding=ROUND_HALF_UP)


@transaction.atomic
def recompute_provider_prices(provider_id):
    """Re-price all of a provider's offerings from their current rating,
    recording every actual change in the audit log."""
    provider = ServiceProvider.objects.select_for_update().get(pk=provider_id)
    multiplier = multiplier_for(provider.rating_avg, provider.rating_count)

    for offering in provider.offerings.all():
        new_price = (offering.base_price * multiplier).quantize(
            _CENTS, rounding=ROUND_HALF_UP,
        )
        if new_price == offering.current_price:
            continue
        PriceChange.objects.create(
            offering=offering,
            old_price=offering.current_price,
            new_price=new_price,
            rating_avg=provider.rating_avg,
            multiplier=multiplier,
        )
        offering.current_price = new_price
        offering.save(update_fields=["current_price", "updated_at"])
