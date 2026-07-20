"""
Providers and their offerings.

`ServiceProvider`  — an individual worker (Zomato-partner style, not an agency),
                     a 1:1 profile hanging off a role=PROVIDER User.
`ServiceOffering`  — the provider-and-category join. This is where PRICE lives,
                     because price is a fact about the pair, not the person or
                     the category alone.
"""

from django.conf import settings
from django.contrib.gis.db import models as gis_models
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator
from django.db import models

from catalog.models import ServiceCategory


class ServiceMode(models.TextChoices):
    CHAT = "CHAT", "Chat"
    ONSITE = "ONSITE", "On-site"


class BookingType(models.TextChoices):
    # The "optional per service" flag: standard jobs are instant-book, complex
    # ones are gated behind a paid consultation.
    INSTANT = "INSTANT", "Instant booking"
    CONSULTATION_REQUIRED = "CONSULTATION_REQUIRED", "Consultation required"


class ServiceProvider(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="provider_profile",
    )
    full_name = models.CharField(max_length=150)
    bio = models.TextField(blank=True)

    # Geo. geography=True means PostGIS measures true distance on the globe in
    # METRES (what "within 5 km" actually means), instead of degrees. SRID 4326
    # is plain lat/lng (GPS). Nullable so onboarding can happen before the
    # provider drops their pin.
    location = gis_models.PointField(geography=True, srid=4326, null=True, blank=True)

    # How far this provider will travel for on-site work — the knob that makes
    # rural (sparse) vs urban (dense) reach work.
    service_radius_km = models.DecimalField(
        max_digits=5, decimal_places=1, default=5,
        validators=[MinValueValidator(0)],
    )

    accepting_bookings = models.BooleanField(default=True)

    # Denormalised, maintained by the review/pricing engine — NOT edited by hand.
    # Search ranks by rating on every query, so we store it instead of
    # re-aggregating all reviews each time.
    rating_avg = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    rating_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.full_name


class ServiceOffering(models.Model):
    provider = models.ForeignKey(
        ServiceProvider, on_delete=models.CASCADE, related_name="offerings",
    )
    # PROTECT: don't let a category be deleted out from under live offerings.
    category = models.ForeignKey(
        ServiceCategory, on_delete=models.PROTECT, related_name="offerings",
    )

    # Money is ALWAYS Decimal, never float (floats lose pennies).
    base_price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)],
    )
    # Written by the pricing engine; starts equal to base_price (see save()).
    current_price = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True,
        validators=[MinValueValidator(0)],
    )

    booking_type = models.CharField(
        max_length=25, choices=BookingType.choices, default=BookingType.INSTANT,
    )
    # Only meaningful when booking_type == CONSULTATION_REQUIRED. Credited
    # against the job total if the customer proceeds (handled in the flow layer).
    consultation_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        validators=[MinValueValidator(0)],
    )

    # A provider may support CHAT and/or ONSITE for one offering. An array is the
    # lean choice on Postgres; a separate table would be overkill for two values.
    supported_modes = ArrayField(
        base_field=models.CharField(max_length=10, choices=ServiceMode.choices),
        default=list,
        help_text="e.g. ['CHAT', 'ONSITE']",
    )

    duration_minutes = models.PositiveIntegerField(default=30)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            # One offering per (provider, category) — a provider prices each
            # service exactly once.
            models.UniqueConstraint(
                fields=["provider", "category"],
                name="unique_provider_category_offering",
            ),
        ]

    def save(self, *args, **kwargs):
        # A brand-new offering is priced at base; the pricing engine moves
        # current_price later as reviews come in.
        if self.current_price is None:
            self.current_price = self.base_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.provider.full_name} — {self.category.name} (₹{self.current_price})"
