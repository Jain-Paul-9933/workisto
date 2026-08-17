"""
Suite-wide fixtures.

Celery runs EAGER for every test. Two reasons, and the second matters more than
the one that made us look:

1. Tests that assert on a task's *effect* — re-pricing after a review lands —
   need it to run inline. Otherwise `.delay()` returns a pending AsyncResult and
   the assertion fires before any work happens. (`test_reviews_reprice_the_offering`
   documented `CELERY_TASK_ALWAYS_EAGER` in a comment, but nothing in the
   committed config ever set it, so the test had never actually passed on a
   clean checkout.)

2. Without eager mode `.delay()` publishes to the **real** broker. In
   development a worker is attached to it, and that worker points at the
   development database — so a test hands it a *test*-database primary key and
   the worker re-prices whichever development row happens to share that id.
   That is not theoretical: a pytest run left three
   `pricing.tasks.recompute_provider_prices_task ... succeeded` entries in the
   worker log, operating on dev data. Nothing was corrupted only because every
   seeded provider sits below MIN_REVIEWS, so the multiplier came out neutral.
   Luck, not a guarantee.

Why this sets the *Django* setting rather than `celery_app.conf`: the app is
configured with `config_from_object("django.conf:settings", namespace="CELERY")`,
which resolves each key through Django settings *live*. Assigning
`celery_app.conf.task_always_eager = True` therefore does nothing at all — the
namespaced lookup keeps returning `settings.CELERY_TASK_ALWAYS_EAGER`. Changing
it at the Django end is what the app actually reads, and pytest-django's
`settings` fixture restores it after each test.
"""

import pytest


@pytest.fixture(autouse=True)
def celery_runs_eagerly(settings):
    settings.CELERY_TASK_ALWAYS_EAGER = True
    # Let a failing task raise into the test instead of vanishing into a result
    # backend nobody reads.
    settings.CELERY_TASK_EAGER_PROPAGATES = True
