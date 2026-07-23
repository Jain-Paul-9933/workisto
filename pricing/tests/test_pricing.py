from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from booking.models import Booking, BookingStatus
from catalog.models import ServiceCategory
from pricing.models import PriceChange
from pricing.services import multiplier_for, recompute_provider_prices
from pricing.tasks import recompute_provider_prices_task
from providers.models import ServiceMode, ServiceOffering, ServiceProvider

User = get_user_model()


# --- The formula (pure, no DB) ---------------------------------------------

@pytest.mark.parametrize("rating,count,expected", [
    (Decimal("5.0"), 2, Decimal("1.00")),   # below MIN_REVIEWS → base price
    (Decimal("5.0"), 3, Decimal("1.20")),   # premium for a great provider
    (Decimal("3.0"), 3, Decimal("1.00")),   # neutral rating → no move
    (Decimal("4.0"), 5, Decimal("1.10")),
    (Decimal("1.0"), 3, Decimal("0.85")),   # would be 0.80, clamped up to floor
])
def test_multiplier_formula(rating, count, expected):
    assert multiplier_for(rating, count) == expected


# --- The engine -------------------------------------------------------------

@pytest.fixture
def provider(db):
    user = User.objects.create_user(
        email="ravi@x.com", password="s3cret-pass-123", role=User.Role.PROVIDER,
    )
    return ServiceProvider.objects.create(user=user, full_name="Ravi")


@pytest.fixture
def offering(provider):
    return ServiceOffering.objects.create(
        provider=provider, category=ServiceCategory.objects.create(name="Haircut"),
        base_price="500.00", supported_modes=[ServiceMode.ONSITE],
    )


def set_rating(provider, avg, count):
    ServiceProvider.objects.filter(pk=provider.pk).update(
        rating_avg=avg, rating_count=count,
    )


@pytest.mark.django_db
def test_recompute_applies_premium_and_audits(provider, offering):
    set_rating(provider, "5.00", 3)

    recompute_provider_prices(provider.id)

    offering.refresh_from_db()
    assert offering.current_price == Decimal("600.00")   # 500 × 1.20
    change = PriceChange.objects.get(offering=offering)
    assert change.old_price == Decimal("500.00")
    assert change.new_price == Decimal("600.00")
    assert change.multiplier == Decimal("1.20")


@pytest.mark.django_db
def test_unrated_provider_stays_at_base_no_audit(provider, offering):
    recompute_provider_prices(provider.id)  # rating_count is 0

    offering.refresh_from_db()
    assert offering.current_price == Decimal("500.00")
    assert not PriceChange.objects.filter(offering=offering).exists()


@pytest.mark.django_db
def test_recompute_is_idempotent(provider, offering):
    set_rating(provider, "5.00", 3)
    recompute_provider_prices(provider.id)
    recompute_provider_prices(provider.id)  # nothing left to change

    assert PriceChange.objects.filter(offering=offering).count() == 1


@pytest.mark.django_db
def test_task_runs_the_engine(provider, offering):
    set_rating(provider, "4.00", 5)

    recompute_provider_prices_task(provider.id)  # call the task directly

    offering.refresh_from_db()
    assert offering.current_price == Decimal("550.00")   # 500 × 1.10


# --- Review → rating → price, end to end ------------------------------------

def make_customer(email):
    return User.objects.create_user(
        email=email, password="s3cret-pass-123", role=User.Role.CUSTOMER,
    )


def completed_booking(customer, offering):
    start = timezone.now() - timedelta(days=1)
    return Booking.objects.create(
        customer=customer, provider=offering.provider, offering=offering,
        mode=ServiceMode.ONSITE, status=BookingStatus.COMPLETED,
        start_at=start, end_at=start + timedelta(minutes=30), price="500.00",
    )


@pytest.mark.django_db
def test_reviews_reprice_the_offering(provider, offering,
                                      django_capture_on_commit_callbacks):
    api = APIClient()
    customers = [make_customer(f"c{i}@x.com") for i in range(3)]
    bookings = [completed_booking(c, offering) for c in customers]

    # The re-pricing task is dispatched on-commit; the fixture runs those
    # callbacks (and CELERY_TASK_ALWAYS_EAGER makes the task execute inline).
    with django_capture_on_commit_callbacks(execute=True):
        for customer, booking in zip(customers, bookings):
            api.force_authenticate(customer)
            resp = api.post("/api/reviews/", {"booking": booking.id, "rating": 5},
                            format="json")
            assert resp.status_code == 201

    provider.refresh_from_db()
    offering.refresh_from_db()
    assert provider.rating_avg == Decimal("5.00")
    assert provider.rating_count == 3
    assert offering.current_price == Decimal("600.00")   # rating drove the price


# --- Price-history endpoint -------------------------------------------------

@pytest.mark.django_db
def test_owner_sees_price_history(provider, offering):
    set_rating(provider, "5.00", 3)
    recompute_provider_prices(provider.id)

    api = APIClient()
    api.force_authenticate(provider.user)
    resp = api.get(f"/api/providers/me/offerings/{offering.id}/price-history/")
    assert resp.status_code == 200
    assert len(resp.data) == 1
    assert resp.data[0]["new_price"] == "600.00"


@pytest.mark.django_db
def test_price_history_is_scoped_to_owner(provider, offering):
    set_rating(provider, "5.00", 3)
    recompute_provider_prices(provider.id)

    intruder = User.objects.create_user(
        email="intruder@x.com", password="s3cret-pass-123", role=User.Role.PROVIDER,
    )
    ServiceProvider.objects.create(user=intruder, full_name="Intruder")
    api = APIClient()
    api.force_authenticate(intruder)
    resp = api.get(f"/api/providers/me/offerings/{offering.id}/price-history/")
    assert resp.status_code == 200
    assert resp.data == []   # can't see another provider's pricing
