from rest_framework import serializers

from booking.models import Booking, BookingStatus

from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    """Public read shape — no customer email, just a display name."""

    reviewer = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ["id", "rating", "comment", "reviewer", "created_at"]
        read_only_fields = fields

    def get_reviewer(self, obj):
        return obj.customer.first_name or "Customer"


class ReviewCreateSerializer(serializers.ModelSerializer):
    booking = serializers.PrimaryKeyRelatedField(queryset=Booking.objects.all())

    class Meta:
        model = Review
        fields = ["id", "booking", "rating", "comment", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_booking(self, booking):
        user = self.context["request"].user
        if booking.customer_id != user.id:
            raise serializers.ValidationError("You can only review your own booking.")
        if booking.status != BookingStatus.COMPLETED:
            raise serializers.ValidationError("You can only review a completed booking.")
        if Review.objects.filter(booking=booking).exists():
            raise serializers.ValidationError("This booking has already been reviewed.")
        return booking

    def create(self, validated_data):
        booking = validated_data["booking"]
        # provider/customer are derived — never client-supplied. The signal on
        # save refreshes the provider's rating aggregate.
        return Review.objects.create(
            booking=booking,
            provider=booking.provider,
            customer=booking.customer,
            rating=validated_data["rating"],
            comment=validated_data.get("comment", ""),
        )


class ReviewUpdateSerializer(serializers.ModelSerializer):
    """Owners may amend their own rating/comment; booking is fixed."""

    class Meta:
        model = Review
        fields = ["id", "booking", "rating", "comment", "created_at"]
        read_only_fields = ["id", "booking", "created_at"]
