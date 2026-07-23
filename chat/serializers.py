from rest_framework import serializers

from .models import ChatMessage


class ChatMessageSerializer(serializers.ModelSerializer):
    sender_email = serializers.CharField(source="sender.email", read_only=True)

    class Meta:
        model = ChatMessage
        fields = ["id", "booking", "sender", "sender_email", "body", "created_at"]
        read_only_fields = fields
