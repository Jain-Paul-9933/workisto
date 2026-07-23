from django.contrib import admin

from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "provider", "status", "start_at", "price")
    list_filter = ("status", "mode")
    search_fields = ("customer__email", "provider__full_name")
    autocomplete_fields = ("customer", "provider", "offering")
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "start_at"
