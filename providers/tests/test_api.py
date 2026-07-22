import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from catalog.models import ServiceCategory
from providers.models import ServiceMode, ServiceOffering, ServiceProvider

User = get_user_model()


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def category(db):
    return ServiceCategory.objects.create(name="Drain Cleaning")


def make_provider_user(email):
    return User.objects.create_user(
        email=email, password="s3cret-pass-123", role=User.Role.PROVIDER,
    )


def make_customer_user(email):
    return User.objects.create_user(
        email=email, password="s3cret-pass-123", role=User.Role.CUSTOMER,
    )


# --- Onboarding -------------------------------------------------------------

@pytest.mark.django_db
def test_provider_onboards_with_location(api):
    api.force_authenticate(make_provider_user("ravi@example.com"))

    resp = api.post(
        "/api/providers/",
        {"full_name": "Ravi", "latitude": 12.97, "longitude": 77.59},
        format="json",
    )
    assert resp.status_code == 201
    assert resp.data["location"] == {"latitude": pytest.approx(12.97),
                                     "longitude": pytest.approx(77.59)}
    assert ServiceProvider.objects.filter(full_name="Ravi").exists()


@pytest.mark.django_db
def test_customer_cannot_onboard_as_provider(api):
    api.force_authenticate(make_customer_user("cust@example.com"))

    resp = api.post("/api/providers/", {"full_name": "Nope"}, format="json")
    assert resp.status_code == 403
    assert not ServiceProvider.objects.exists()


@pytest.mark.django_db
def test_onboarding_is_once_only(api):
    user = make_provider_user("ravi@example.com")
    ServiceProvider.objects.create(user=user, full_name="Ravi")
    api.force_authenticate(user)

    resp = api.post("/api/providers/", {"full_name": "Ravi Again"}, format="json")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_lat_lng_must_come_as_a_pair(api):
    api.force_authenticate(make_provider_user("ravi@example.com"))

    resp = api.post(
        "/api/providers/",
        {"full_name": "Ravi", "latitude": 12.97},  # missing longitude
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_provider_updates_own_profile(api):
    user = make_provider_user("ravi@example.com")
    ServiceProvider.objects.create(user=user, full_name="Ravi")
    api.force_authenticate(user)

    resp = api.patch(
        "/api/providers/me/",
        {"bio": "20 years of drains", "accepting_bookings": False},
        format="json",
    )
    assert resp.status_code == 200
    assert resp.data["bio"] == "20 years of drains"
    assert resp.data["accepting_bookings"] is False


@pytest.mark.django_db
def test_rating_is_read_only_over_the_api(api):
    user = make_provider_user("ravi@example.com")
    ServiceProvider.objects.create(user=user, full_name="Ravi")
    api.force_authenticate(user)

    resp = api.patch("/api/providers/me/", {"rating_avg": "5.00"}, format="json")
    assert resp.status_code == 200
    assert resp.data["rating_avg"] == "0.00"  # engine-owned, ignored on input


# --- Offerings --------------------------------------------------------------

@pytest.mark.django_db
def test_create_offering(api, category):
    user = make_provider_user("ravi@example.com")
    ServiceProvider.objects.create(user=user, full_name="Ravi")
    api.force_authenticate(user)

    resp = api.post(
        "/api/providers/me/offerings/",
        {
            "category": category.id,
            "base_price": "500.00",
            "supported_modes": [ServiceMode.ONSITE],
        },
        format="json",
    )
    assert resp.status_code == 201
    assert resp.data["current_price"] == "500.00"  # defaults to base on create
    assert resp.data["category_name"] == "Drain Cleaning"


@pytest.mark.django_db
def test_duplicate_offering_rejected(api, category):
    user = make_provider_user("ravi@example.com")
    provider = ServiceProvider.objects.create(user=user, full_name="Ravi")
    ServiceOffering.objects.create(
        provider=provider, category=category, base_price="500.00",
        supported_modes=[ServiceMode.ONSITE],
    )
    api.force_authenticate(user)

    resp = api.post(
        "/api/providers/me/offerings/",
        {"category": category.id, "base_price": "600.00",
         "supported_modes": [ServiceMode.CHAT]},
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_offering_needs_at_least_one_mode(api, category):
    user = make_provider_user("ravi@example.com")
    ServiceProvider.objects.create(user=user, full_name="Ravi")
    api.force_authenticate(user)

    resp = api.post(
        "/api/providers/me/offerings/",
        {"category": category.id, "base_price": "500.00", "supported_modes": []},
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_provider_cannot_touch_another_providers_offering(api, category):
    owner = make_provider_user("owner@example.com")
    owner_provider = ServiceProvider.objects.create(user=owner, full_name="Owner")
    offering = ServiceOffering.objects.create(
        provider=owner_provider, category=category, base_price="500.00",
        supported_modes=[ServiceMode.ONSITE],
    )

    intruder = make_provider_user("intruder@example.com")
    ServiceProvider.objects.create(user=intruder, full_name="Intruder")
    api.force_authenticate(intruder)

    # Scoped queryset means the intruder can't even see it → 404, not 403.
    assert api.get(f"/api/providers/me/offerings/{offering.id}/").status_code == 404
    assert api.delete(f"/api/providers/me/offerings/{offering.id}/").status_code == 404
    assert offering.__class__.objects.filter(id=offering.id).exists()


@pytest.mark.django_db
def test_offerings_list_shows_only_own(api, category):
    owner = make_provider_user("owner@example.com")
    owner_provider = ServiceProvider.objects.create(user=owner, full_name="Owner")
    ServiceOffering.objects.create(
        provider=owner_provider, category=category, base_price="500.00",
        supported_modes=[ServiceMode.ONSITE],
    )

    other = make_provider_user("other@example.com")
    other_provider = ServiceProvider.objects.create(user=other, full_name="Other")
    other_cat = ServiceCategory.objects.create(name="Haircut")
    ServiceOffering.objects.create(
        provider=other_provider, category=other_cat, base_price="200.00",
        supported_modes=[ServiceMode.ONSITE],
    )

    api.force_authenticate(owner)
    resp = api.get("/api/providers/me/offerings/")
    assert resp.status_code == 200
    assert len(resp.data) == 1
    assert resp.data[0]["category_name"] == "Drain Cleaning"
