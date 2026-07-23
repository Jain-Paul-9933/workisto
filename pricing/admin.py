from django.contrib import admin

from .models import PriceChange


@admin.register(PriceChange)
class PriceChangeAdmin(admin.ModelAdmin):
    list_display = ("id", "offering", "old_price", "new_price", "multiplier", "created_at")
    search_fields = ("offering__provider__full_name", "offering__category__name")
    readonly_fields = ("offering", "old_price", "new_price", "rating_avg",
                       "multiplier", "created_at")

    def has_add_permission(self, request):
        return False  # audit rows are engine-written only
