from django.urls import path

from .views import (
    ProviderMeView,
    ProviderOfferingDetailView,
    ProviderOfferingsView,
    ProviderOnboardView,
    ProviderSearchView,
    PublicProviderDetailView,
)

app_name = "providers"

urlpatterns = [
    path("providers/", ProviderOnboardView.as_view(), name="provider-onboard"),
    # Literal segments must precede the <int:pk> catch-all below.
    path("providers/search/", ProviderSearchView.as_view(), name="provider-search"),
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
    path(
        "providers/<int:pk>/",
        PublicProviderDetailView.as_view(),
        name="provider-detail",
    ),
]
