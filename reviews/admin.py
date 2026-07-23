from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("id", "provider", "customer", "rating", "created_at")
    list_filter = ("rating",)
    search_fields = ("provider__full_name", "customer__email")
    autocomplete_fields = ("booking", "provider", "customer")
    readonly_fields = ("created_at", "updated_at")
