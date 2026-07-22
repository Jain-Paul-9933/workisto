from django.urls import path

from .views import (
    ProviderMeView,
    ProviderOfferingDetailView,
    ProviderOfferingsView,
    ProviderOnboardView,
)

app_name = "providers"

urlpatterns = [
    path("providers/", ProviderOnboardView.as_view(), name="provider-onboard"),
    path("providers/me/", ProviderMeView.as_view(), name="provider-me"),
    path(
        "providers/me/offerings/",
        ProviderOfferingsView.as_view(),
        name="provider-offerings",
    ),
    path(
        "providers/me/offerings/<int:pk>/",
        ProviderOfferingDetailView.as_view(),
        name="provider-offering-detail",
    ),
]
