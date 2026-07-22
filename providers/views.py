"""
Provider self-service endpoints. Everything here is scoped to the *caller*:

- `IsProvider` gates the whole surface to authenticated PROVIDER users.
- Every queryset is filtered to `request.user`, which is also the object-level
  guard — a provider literally cannot address another provider's row, so
  retrieve/update/delete on someone else's offering 404s instead of leaking it.
"""

from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404

from accounts.permissions import IsProvider

from .models import ServiceOffering, ServiceProvider
from .serializers import ServiceOfferingSerializer, ServiceProviderSerializer


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
