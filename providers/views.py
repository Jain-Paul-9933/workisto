"""
Provider self-service endpoints. Everything here is scoped to the *caller*:

- `IsProvider` gates the whole surface to authenticated PROVIDER users.
- Every queryset is filtered to `request.user`, which is also the object-level
  guard — a provider literally cannot address another provider's row, so
  retrieve/update/delete on someone else's offering 404s instead of leaking it.
"""

from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny

from accounts.permissions import IsProvider

from .models import ServiceMode, ServiceOffering, ServiceProvider
from .serializers import (
    ProviderSearchSerializer,
    PublicProviderSerializer,
    ServiceOfferingSerializer,
    ServiceProviderSerializer,
)


class ProviderOnboardView(generics.CreateAPIView):
    """POST /api/providers/ — create the caller's own profile, exactly once."""

    serializer_class = ServiceProviderSerializer
    permission_classes = [IsProvider]

    def perform_create(self, serializer):
        if ServiceProvider.objects.filter(user=self.request.user).exists():
            raise ValidationError("You already have a provider profile.")
        serializer.save(user=self.request.user)


class ProviderMeView(generics.RetrieveUpdateAPIView):
    """GET / PATCH /api/providers/me/ — the caller's own profile."""

    serializer_class = ServiceProviderSerializer
    permission_classes = [IsProvider]

    def get_object(self):
        return get_object_or_404(ServiceProvider, user=self.request.user)


class ProviderOfferingsView(generics.ListCreateAPIView):
    """GET / POST /api/providers/me/offerings/ — the caller's own offerings."""

    serializer_class = ServiceOfferingSerializer
    permission_classes = [IsProvider]

    def get_queryset(self):
        return ServiceOffering.objects.filter(provider__user=self.request.user)

    def perform_create(self, serializer):
        provider = get_object_or_404(ServiceProvider, user=self.request.user)
        category = serializer.validated_data["category"]
        # Surface the unique (provider, category) rule as a clean 400, not a
        # database IntegrityError bubbling up as a 500.
        if ServiceOffering.objects.filter(provider=provider, category=category).exists():
            raise ValidationError({"category": "You already offer this service."})
        serializer.save(provider=provider)


class ProviderOfferingDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET / PATCH / DELETE /api/providers/me/offerings/{id}/ — one own offering."""

    serializer_class = ServiceOfferingSerializer
    permission_classes = [IsProvider]

    def get_queryset(self):
        return ServiceOffering.objects.filter(provider__user=self.request.user)


# --- Public discovery -------------------------------------------------------

class ProviderSearchView(generics.ListAPIView):
    """GET /api/providers/search/ — find bookable providers near a point.

    Params: lat, lng (required); category (slug), mode (CHAT/ONSITE), radius_km
    (default 10, capped at 50) — all optional. Results are ranked by rating,
    then by proximity, with the distance to each provider annotated in.
    """

    serializer_class = ProviderSearchSerializer
    permission_classes = [AllowAny]

    DEFAULT_RADIUS_KM = 10.0
    MAX_RADIUS_KM = 50.0

    def get_queryset(self):
        params = self.request.query_params
        point = self._point(params)
        radius_km = self._radius(params)

        # All the offering conditions go in ONE filter() call so they must be
        # satisfied by the SAME offering — a provider who does drains onsite and
        # something-else via chat must not match "drains via chat". Separate
        # filter() calls would join the reverse relation twice and let that slip.
        offering_match = {"offerings__is_active": True}
        category = params.get("category")
        if category:
            offering_match["offerings__category__slug"] = category
        mode = params.get("mode")
        if mode:
            mode = mode.upper()
            if mode not in ServiceMode.values:
                raise ValidationError(
                    {"mode": f"Must be one of {list(ServiceMode.values)}."}
                )
            offering_match["offerings__supported_modes__contains"] = [mode]

        return (
            ServiceProvider.objects
            .filter(location__isnull=False, accepting_bookings=True)
            # dwithin hits the GiST index on the geography column — the cheap
            # bounding filter runs before the exact distance is ever computed.
            .filter(location__dwithin=(point, D(km=radius_km)))
            .filter(**offering_match)
            .annotate(distance=Distance("location", point))
            .distinct()  # a provider with several matching offerings is still one hit
            .order_by("-rating_avg", "distance")
        )

    def _point(self, params):
        try:
            lat = float(params["lat"])
            lng = float(params["lng"])
        except KeyError:
            raise ValidationError("lat and lng query params are required.")
        except ValueError:
            raise ValidationError("lat and lng must be numbers.")
        if not (-90 <= lat <= 90 and -180 <= lng <= 180):
            raise ValidationError("lat/lng out of range.")
        return Point(lng, lat, srid=4326)

    def _radius(self, params):
        try:
            radius = float(params.get("radius_km", self.DEFAULT_RADIUS_KM))
        except ValueError:
            raise ValidationError({"radius_km": "Must be a number."})
        if radius <= 0:
            raise ValidationError({"radius_km": "Must be positive."})
        return min(radius, self.MAX_RADIUS_KM)


class PublicProviderDetailView(generics.RetrieveAPIView):
    """GET /api/providers/{id}/ — a provider's public profile + active offerings."""

    queryset = ServiceProvider.objects.all()
    serializer_class = PublicProviderSerializer
    permission_classes = [AllowAny]
