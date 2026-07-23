"""
Pricing has no domain nouns of its own — it prices `providers.ServiceOffering`.
What it *does* own is an audit trail: every time the engine moves a price, it
records why (the rating and multiplier that drove it), so "why did my price
change?" has a concrete answer.
"""

from django.db import models

from providers.models import ServiceOffering


class PriceChange(models.Model):
    offering = models.ForeignKey(
        ServiceOffering, on_delete=models.CASCADE, related_name="price_changes",
    )
    old_price = models.DecimalField(max_digits=10, decimal_places=2)
    new_price = models.DecimalField(max_digits=10, decimal_places=2)
    # The inputs that produced new_price, snapshotted for the audit.
    rating_avg = models.DecimalField(max_digits=3, decimal_places=2)
    multiplier = models.DecimalField(max_digits=4, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"offering {self.offering_id}: {self.old_price} → {self.new_price}"
