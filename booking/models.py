"""
Bookings — the transactional heart of the marketplace.

Two paths converge on the same row:

- **Instant** offerings: the customer picks a slot and the booking is created
  straight to CONFIRMED (after the slot-safety check).
- **Consultation-required** offerings: the customer files a request
  (PENDING_ESTIMATE), the provider quotes (ESTIMATED), and the customer accepts
  with a chosen slot (CONFIRMED).

`provider` is denormalised off `offering` on purpose: every slot-overlap query
and the row lock that guards it filter by provider, so we keep it one join
closer. Money fields are snapshots recorded here; actually *charging* them is
the payments increment.
"""

from django.conf import settings
from django.db import models
from django.db.models import F, Q

from providers.models import ServiceMode, ServiceOffering, ServiceProvider


class BookingStatus(models.TextChoices):
    PENDING_ESTIMATE = "PENDING_ESTIMATE", "Pending estimate"
    ESTIMATED = "ESTIMATED", "Estimate provided"
    CONFIRMED = "CONFIRMED", "Confirmed"
    CANCELLED = "CANCELLED", "Cancelled"
    COMPLETED = "COMPLETED", "Completed"


# Statuses that actually occupy a provider's calendar. Only these block a slot;
# a cancelled booking frees it, a pending-estimate one never held it.
BLOCKING_STATUSES = [BookingStatus.CONFIRMED]


class Booking(models.Model):
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="bookings",
    )
    provider = models.ForeignKey(
        ServiceProvider, on_delete=models.PROTECT, related_name="bookings",
    )
    offering = models.ForeignKey(
        ServiceOffering, on_delete=models.PROTECT, related_name="bookings",
    )
    mode = models.CharField(max_length=10, choices=ServiceMode.choices)
    status = models.CharField(max_length=20, choices=BookingStatus.choices)

    # Null until a slot is actually reserved (consultation requests have none yet).
    start_at = models.DateTimeField(null=True, blank=True)
    end_at = models.DateTimeField(null=True, blank=True)

    # Money snapshots (charged later, in the payments increment).
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estimate_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
    )

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            # The exact shape of the overlap query in services.reserve logic.
            models.Index(fields=["provider", "status", "start_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                name="booking_end_after_start",
                condition=Q(start_at__isnull=True) | Q(end_at__gt=F("start_at")),
            ),
        ]

    def __str__(self):
        return f"Booking #{self.pk} — {self.provider} ({self.status})"
