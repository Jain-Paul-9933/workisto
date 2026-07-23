from django.utils import timezone
from rest_framework import serializers

from providers.models import BookingType, ServiceOffering

from .models import Booking


def _reject_past(when):
    if when <= timezone.now():
        raise serializers.ValidationError("Must be a time in the future.")
    return when


class BookingSerializer(serializers.ModelSerializer):
    """The read shape of a booking, for both parties."""

    provider_name = serializers.CharField(source="provider.full_name", read_only=True)
    category_name = serializers.CharField(source="offering.category.name", read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id", "customer", "provider", "provider_name", "offering",
            "category_name", "mode", "status", "start_at", "end_at", "price",
            "consultation_fee", "estimate_amount", "notes", "created_at",
        ]
        read_only_fields = fields


class BookingCreateSerializer(serializers.Serializer):
    offering = serializers.PrimaryKeyRelatedField(
        queryset=ServiceOffering.objects.filter(is_active=True),
    )
    mode = serializers.CharField()
    start_at = serializers.DateTimeField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, attrs):
        offering = attrs["offering"]
        if attrs["mode"] not in offering.supported_modes:
            raise serializers.ValidationError(
                {"mode": "This offering does not support that mode."}
            )
        if not offering.provider.accepting_bookings:
            raise serializers.ValidationError("This provider is not accepting bookings.")
        # Instant bookings reserve a slot right now, so they need the time up
        # front; consultation requests get their slot later, at confirm.
        if offering.booking_type == BookingType.INSTANT:
            if not attrs.get("start_at"):
                raise serializers.ValidationError(
                    {"start_at": "Required for an instant booking."}
                )
            _reject_past(attrs["start_at"])
        return attrs


class EstimateSerializer(serializers.Serializer):
    estimate_amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, min_value=0,
    )


class ConfirmSerializer(serializers.Serializer):
    start_at = serializers.DateTimeField()

    def validate_start_at(self, value):
        return _reject_past(value)
