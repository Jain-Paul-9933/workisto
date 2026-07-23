from celery import shared_task

from .services import recompute_provider_prices


@shared_task
def recompute_provider_prices_task(provider_id):
    """Off-the-request-path re-pricing. Kicked off after a provider's rating
    changes (see signals.py); the request that triggered it doesn't wait."""
    recompute_provider_prices(provider_id)
