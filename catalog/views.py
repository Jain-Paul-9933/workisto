"""
Catalog is read-only over the API: the service taxonomy is curated by admins in
Django admin, and everyone else (customers browsing before they even sign up,
providers picking what to offer) only reads it. Hence AllowAny + list/detail.
"""

from rest_framework import generics
from rest_framework.permissions import AllowAny

from .models import ServiceCategory
from .serializers import ServiceCategorySerializer


class ServiceCategoryListView(generics.ListAPIView):
    queryset = ServiceCategory.objects.filter(is_active=True)
    serializer_class = ServiceCategorySerializer
    permission_classes = [AllowAny]


class ServiceCategoryDetailView(generics.RetrieveAPIView):
    queryset = ServiceCategory.objects.filter(is_active=True)
    serializer_class = ServiceCategorySerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"
