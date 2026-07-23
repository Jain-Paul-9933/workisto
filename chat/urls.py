from django.urls import path

from .views import BookingMessagesView

app_name = "chat"

urlpatterns = [
    path(
        "bookings/<int:pk>/messages/",
        BookingMessagesView.as_view(),
        name="booking-messages",
    ),
]
