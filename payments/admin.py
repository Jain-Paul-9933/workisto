from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "booking", "kind", "amount", "currency", "status", "created_at")
    list_filter = ("kind", "status", "currency")
    search_fields = ("external_id", "booking__customer__email")
    autocomplete_fields = ("booking",)
    readonly_fields = ("external_id", "client_secret", "created_at", "updated_at")
