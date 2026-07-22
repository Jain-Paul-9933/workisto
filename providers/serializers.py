"""
Serializers for provider self-service.

Two deliberate shapes:
- Location crosses the API as plain `latitude`/`longitude` (what a map widget
  hands you), not WKT/GeoJSON — the PostGIS `Point` is an implementation detail
  the frontend shouldn't have to know.
- Engine-owned fields (`current_price`, `rating_avg`, `rating_count`) are
  read-only here; only the pricing/review engines write them.
"""

from django.contrib.gis.geos import Point
from rest_framework import serializers

from catalog.models import ServiceCategory

from .models import ServiceMode, ServiceOffering, ServiceProvider


class ServiceProviderSerializer(serializers.ModelSerializer):
    # Write side: a lat/lng pair. Read side: the `location` dict below.
    latitude = serializers.FloatField(write_only=True, required=False, allow_null=True)
    longitude = serializers.FloatField(write_only=True, required=False, allow_null=True)
    location = serializers.SerializerMethodField()

    class Meta:
        model = ServiceProvider
        fields = [
            "id", "full_name", "bio", "service_radius_km", "accepting_bookings",
            "rating_avg", "rating_count", "location", "latitude", "longitude",
            "created_at",
        ]
        read_only_fields = ["id", "rating_avg", "rating_count", "created_at"]

    def get_location(self, obj):
        # PostGIS Point is (x=lng, y=lat); present it the human way round.
        if obj.location is None:
            return None
        return {"latitude": obj.location.y, "longitude": obj.location.x}

    def validate(self, attrs):
        lat = attrs.pop("latitude", None)
        lng = attrs.pop("longitude", None)
        if lat is not None and lng is not None:
            attrs["location"] = Point(lng, lat, srid=4326)
        elif (lat is None) != (lng is None):
            raise serializers.ValidationError(
                "latitude and longitude must be provided together."
            )
        # Neither given → leave location untouched (onboarding can happen before
        # the provider drops their pin).
        return attrs


class ServiceOfferingSerializer(serializers.ModelSerializer):
    # Only active categories can be offered. `provider` is never client-supplied;
    # the view pins it to the caller.
    category = serializers.PrimaryKeyRelatedField(
        queryset=ServiceCategory.objects.filter(is_active=True),
    )
    category_name = serializers.CharField(source="category.name", read_only=True)
    supported_modes = serializers.ListField(
        child=serializers.ChoiceField(choices=ServiceMode.choices),
        allow_empty=False,  # an offering nobody can book any way is meaningless
    )

    class Meta:
        model = ServiceOffering
        fields = [
            "id", "category", "category_name", "base_price", "current_price",
            "booking_type", "consultation_fee", "supported_modes",
            "duration_minutes", "is_active",
        ]
        read_only_fields = ["id", "current_price", "category_name"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # An offering IS the (provider, category) pairing — category is its
        # identity. Set once at creation, immutable after; to offer a different
        # service, create another offering.
        if isinstance(self.instance, ServiceOffering):
            self.fields["category"].read_only = True
