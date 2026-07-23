"""
Reviews.

A review hangs off a **booking**, one-to-one — you review a job you actually had
done, not a provider in the abstract, and a customer who books the same provider
twice leaves two reviews. `provider` and `customer` are denormalised off the
booking so rating aggregation and public "reviews for provider X" listings are a
single-table query.

The provider's `rating_avg` / `rating_count` are NOT edited here directly; a
signal recomputes them from the reviews whenever one changes (see signals.py and
services.recompute_provider_rating). Those denormalised fields are what
provider-search ranks by.
"""

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from booking.models import Booking
from providers.models import ServiceProvider


class Review(models.Model):
    booking = models.OneToOneField(
        Booking, on_delete=models.CASCADE, related_name="review",
    )
    provider = models.ForeignKey(
        ServiceProvider, on_delete=models.CASCADE, related_name="reviews",
    )
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews",
    )

    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    comment = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.rating}★ for {self.provider} (booking #{self.booking_id})"
