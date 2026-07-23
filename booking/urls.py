from django.urls import path

from .views import (
    BookingCancelView,
    BookingCompleteView,
    BookingConfirmView,
    BookingDetailView,
    BookingEstimateView,
    BookingListCreateView,
)

app_name = "booking"

urlpatterns = [
    path("bookings/", BookingListCreateView.as_view(), name="booking-list"),
    path("bookings/<int:pk>/", BookingDetailView.as_view(), name="booking-detail"),
    path("bookings/<int:pk>/estimate/", BookingEstimateView.as_view(), name="booking-estimate"),
    path("bookings/<int:pk>/confirm/", BookingConfirmView.as_view(), name="booking-confirm"),
    path("bookings/<int:pk>/cancel/", BookingCancelView.as_view(), name="booking-cancel"),
    path("bookings/<int:pk>/complete/", BookingCompleteView.as_view(), name="booking-complete"),
]
