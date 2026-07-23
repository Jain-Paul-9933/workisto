"""
Payments against a booking.

Three kinds of money change hands over a job's life:
- CONSULTATION — the paid consultation fee (for consultation-required jobs),
  later credited against the total.
- ADVANCE — a deposit taken up front on a confirmed job.
- FINAL — the remainder, net of the advance and any consultation credit.

A `Payment` row mirrors a Stripe PaymentIntent. It's created PENDING when we ask
Stripe for an intent, and only flips to SUCCEEDED when Stripe tells us so via a
signed webhook — never on the strength of the client saying "it worked".
"""

from django.db import models
from django.db.models import Q

from booking.models import Booking


class PaymentKind(models.TextChoices):
    CONSULTATION = "CONSULTATION", "Consultation fee"
    ADVANCE = "ADVANCE", "Advance"
    FINAL = "FINAL", "Final"


class PaymentStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    SUCCEEDED = "SUCCEEDED", "Succeeded"
    FAILED = "FAILED", "Failed"
    REFUNDED = "REFUNDED", "Refunded"


class Payment(models.Model):
    booking = models.ForeignKey(
        Booking, on_delete=models.PROTECT, related_name="payments",
    )
    kind = models.CharField(max_length=20, choices=PaymentKind.choices)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="inr")
    status = models.CharField(
        max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING,
    )

    # The Stripe PaymentIntent id — our link back when a webhook arrives.
    external_id = models.CharField(max_length=255, blank=True, db_index=True)
    # Handed to the client so it can complete the payment; not a secret we store
    # long-term, but convenient to keep on the pending row.
    client_secret = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            # At most one *successful* payment of a given kind per booking —
            # enforced by the DB, not just checked in code.
            models.UniqueConstraint(
                fields=["booking", "kind"],
                condition=Q(status="SUCCEEDED"),
                name="one_successful_payment_per_booking_kind",
            ),
        ]

    def __str__(self):
        return f"{self.kind} {self.amount} {self.currency} ({self.status})"
