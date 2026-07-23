"""
Ratings drive prices, one step removed. When a review changes a provider's
rating (the reviews app recomputes `rating_avg` synchronously), we enqueue a
re-pricing task rather than doing it inline — pricing is not on the critical
path of leaving a review.

`transaction.on_commit` is the important detail: we dispatch the task only after
the surrounding transaction commits, so the worker reads the *new* rating, never
a value that might still get rolled back.
"""

from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from reviews.models import Review

from .tasks import recompute_provider_prices_task


def _enqueue(provider_id):
    transaction.on_commit(
        lambda: recompute_provider_prices_task.delay(provider_id)
    )


@receiver(post_save, sender=Review)
def reprice_on_review_saved(sender, instance, **kwargs):
    _enqueue(instance.provider_id)


@receiver(post_delete, sender=Review)
def reprice_on_review_deleted(sender, instance, **kwargs):
    _enqueue(instance.provider_id)
