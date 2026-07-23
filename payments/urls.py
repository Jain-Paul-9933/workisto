from django.urls import path

from .views import BookingPaymentsView, BookingPayView, StripeWebhookView

app_name = "payments"

urlpatterns = [
    path("bookings/<int:pk>/pay/", BookingPayView.as_view(), name="booking-pay"),
    path("bookings/<int:pk>/payments/", BookingPaymentsView.as_view(), name="booking-payments"),
    path("payments/webhook/", StripeWebhookView.as_view(), name="stripe-webhook"),
]
