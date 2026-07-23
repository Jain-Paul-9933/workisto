from rest_framework import serializers

from .models import PriceChange


class PriceChangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceChange
        fields = ["id", "old_price", "new_price", "rating_avg", "multiplier", "created_at"]
        read_only_fields = fields
