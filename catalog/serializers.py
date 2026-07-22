from rest_framework import serializers

from .models import ServiceCategory


class ServiceCategorySerializer(serializers.ModelSerializer):
    """Read-only public shape of a category. The taxonomy is admin-managed;
    the API only ever reads it (see catalog.views)."""

    class Meta:
        model = ServiceCategory
        fields = ["id", "name", "slug", "description", "default_duration_minutes"]
        read_only_fields = fields
