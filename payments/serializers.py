from rest_framework import serializers

from .models import Payment, PaymentKind


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "id", "booking", "kind", "amount", "currency", "status",
            "client_secret", "created_at",
        ]
        read_only_fields = fields


class PayRequestSerializer(serializers.Serializer):
    kind = serializers.ChoiceField(choices=PaymentKind.choices)
