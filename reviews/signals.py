"""
Keep ServiceProvider.rating_* in lockstep with the reviews — no matter where a
review is created, edited, or deleted (API, admin, data migration). A signal
can't be bypassed the way a service-call convention can.
"""

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Review
from .services import recompute_provider_rating


@receiver(post_save, sender=Review)
def recompute_on_save(sender, instance, **kwargs):
    recompute_provider_rating(instance.provider_id)


@receiver(post_delete, sender=Review)
def recompute_on_delete(sender, instance, **kwargs):
    recompute_provider_rating(instance.provider_id)
