from django.contrib import admin

from .models import ServiceOffering, ServiceProvider


class ServiceOfferingInline(admin.TabularInline):
    model = ServiceOffering
    extra = 1
    fields = ("category", "base_price", "current_price", "booking_type",
              "consultation_fee", "supported_modes", "duration_minutes", "is_active")
    readonly_fields = ("current_price",)


@admin.register(ServiceProvider)
class ServiceProviderAdmin(admin.ModelAdmin):
    list_display = ("full_name", "user", "accepting_bookings",
                    "rating_avg", "rating_count")
    list_filter = ("accepting_bookings",)
    search_fields = ("full_name", "user__email")
    readonly_fields = ("rating_avg", "rating_count")  # engine-maintained
    inlines = [ServiceOfferingInline]


@admin.register(ServiceOffering)
class ServiceOfferingAdmin(admin.ModelAdmin):
    list_display = ("provider", "category", "base_price", "current_price",
                    "booking_type", "is_active")
    list_filter = ("booking_type", "is_active", "category")
    search_fields = ("provider__full_name", "category__name")
    readonly_fields = ("current_price",)
