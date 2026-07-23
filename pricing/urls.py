from django.urls import path

from .views import OfferingPriceHistoryView

app_name = "pricing"

urlpatterns = [
    path(
        "providers/me/offerings/<int:pk>/price-history/",
        OfferingPriceHistoryView.as_view(),
        name="offering-price-history",
    ),
]
