from django.urls import path

from .views import ProviderReviewListView, ReviewCreateView, ReviewDetailView

app_name = "reviews"

urlpatterns = [
    path("reviews/", ReviewCreateView.as_view(), name="review-create"),
    path("reviews/<int:pk>/", ReviewDetailView.as_view(), name="review-detail"),
    path(
        "providers/<int:pk>/reviews/",
        ProviderReviewListView.as_view(),
        name="provider-reviews",
    ),
]
