import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from catalog.models import ServiceCategory
from providers.models import ServiceMode, ServiceOffering, ServiceProvider

User = get_user_model()


@pytest.fixture
def provider(db):
    user = User.objects.create_user(
        email="ravi@example.com", password="pw", role=User.Role.PROVIDER,
    )
    return ServiceProvider.objects.create(user=user, full_name="Ravi")


@pytest.fixture
def category(db):
    return ServiceCategory.objects.create(name="Drain Cleaning")


def test_current_price_defaults_to_base_price(provider, category):
    offering = ServiceOffering.objects.create(
        provider=provider, category=category, base_price="500.00",
        supported_modes=[ServiceMode.ONSITE],
    )
    assert offering.current_price == offering.base_price


def test_one_offering_per_provider_and_category(provider, category):
    ServiceOffering.objects.create(
        provider=provider, category=category, base_price="500.00",
        supported_modes=[ServiceMode.CHAT],
    )
    # Same provider + same category a second time must be rejected by the DB.
    with pytest.raises(IntegrityError):
        ServiceOffering.objects.create(
            provider=provider, category=category, base_price="600.00",
            supported_modes=[ServiceMode.CHAT],
        )
