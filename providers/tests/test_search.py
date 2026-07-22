import pytest
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from rest_framework.test import APIClient

from catalog.models import ServiceCategory
from providers.models import ServiceMode, ServiceOffering, ServiceProvider

User = get_user_model()

# A customer standing in central Bengaluru.
CUSTOMER_LAT, CUSTOMER_LNG = 12.9716, 77.5946


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def drains(db):
    return ServiceCategory.objects.create(name="Drain Cleaning")


def make_provider(email, name, lat, lng, *, rating="0.00", accepting=True):
    user = User.objects.create_user(
        email=email, password="s3cret-pass-123", role=User.Role.PROVIDER,
    )
    return ServiceProvider.objects.create(
        user=user, full_name=name, location=Point(lng, lat, srid=4326),
        rating_avg=rating, accepting_bookings=accepting,
    )


def add_offering(provider, category, modes, *, active=True):
    return ServiceOffering.objects.create(
        provider=provider, category=category, base_price="500.00",
        supported_modes=modes, is_active=active,
    )


def search(api, **params):
    params.setdefault("lat", CUSTOMER_LAT)
    params.setdefault("lng", CUSTOMER_LNG)
    return api.get("/api/providers/search/", params)


@pytest.mark.django_db
def test_nearby_included_far_excluded(api, drains):
    near = make_provider("near@x.com", "Near", 12.98, 77.59)      # ~1 km
    add_offering(near, drains, [ServiceMode.ONSITE])
    far = make_provider("far@x.com", "Far", 13.60, 77.59)         # ~70 km
    add_offering(far, drains, [ServiceMode.ONSITE])

    resp = search(api, category="drain-cleaning")  # default radius 10 km
    assert resp.status_code == 200
    names = [p["full_name"] for p in resp.data]
    assert names == ["Near"]
    assert resp.data[0]["distance_km"] < 5


@pytest.mark.django_db
def test_ranked_by_rating_then_distance(api, drains):
    close_low = make_provider("a@x.com", "CloseLow", 12.975, 77.594, rating="3.0")
    add_offering(close_low, drains, [ServiceMode.ONSITE])
    far_high = make_provider("b@x.com", "FarHigh", 13.05, 77.60, rating="4.5")  # farther
    add_offering(far_high, drains, [ServiceMode.ONSITE])

    resp = search(api, category="drain-cleaning")
    # Rating wins over proximity: the 4.5 provider ranks first despite being farther.
    assert [p["full_name"] for p in resp.data] == ["FarHigh", "CloseLow"]


@pytest.mark.django_db
def test_filters_by_category(api, drains):
    haircut = ServiceCategory.objects.create(name="Haircut")
    p = make_provider("p@x.com", "Barber", 12.98, 77.59)
    add_offering(p, haircut, [ServiceMode.ONSITE])  # offers haircut, not drains

    resp = search(api, category="drain-cleaning")
    assert resp.data == []


@pytest.mark.django_db
def test_filters_by_mode(api, drains):
    p = make_provider("p@x.com", "OnsiteOnly", 12.98, 77.59)
    add_offering(p, drains, [ServiceMode.ONSITE])  # no chat

    assert search(api, category="drain-cleaning", mode="CHAT").data == []
    assert len(search(api, category="drain-cleaning", mode="ONSITE").data) == 1


@pytest.mark.django_db
def test_excludes_not_accepting_and_no_active_offering(api, drains):
    paused = make_provider("paused@x.com", "Paused", 12.98, 77.59, accepting=False)
    add_offering(paused, drains, [ServiceMode.ONSITE])
    dormant = make_provider("dormant@x.com", "Dormant", 12.98, 77.59)
    add_offering(dormant, drains, [ServiceMode.ONSITE], active=False)
    no_offering = make_provider("bare@x.com", "Bare", 12.98, 77.59)  # no offerings

    resp = search(api, category="drain-cleaning")
    assert resp.data == []


@pytest.mark.django_db
def test_category_match_must_be_one_offering(api, drains):
    """A provider who does drains ONSITE and haircuts via CHAT must not match
    'drains via chat' — the join must land on a single offering."""
    haircut = ServiceCategory.objects.create(name="Haircut")
    p = make_provider("p@x.com", "Mixed", 12.98, 77.59)
    add_offering(p, drains, [ServiceMode.ONSITE])
    add_offering(p, haircut, [ServiceMode.CHAT])

    assert search(api, category="drain-cleaning", mode="CHAT").data == []
    assert len(search(api, category="drain-cleaning", mode="ONSITE").data) == 1


@pytest.mark.django_db
def test_one_hit_per_provider_despite_multiple_offerings(api, drains):
    haircut = ServiceCategory.objects.create(name="Haircut")
    p = make_provider("p@x.com", "Busy", 12.98, 77.59)
    add_offering(p, drains, [ServiceMode.ONSITE])
    add_offering(p, haircut, [ServiceMode.ONSITE])

    resp = search(api)  # no category → both offerings match the active filter
    assert len(resp.data) == 1


@pytest.mark.django_db
def test_lat_lng_required(api):
    assert api.get("/api/providers/search/").status_code == 400
    assert api.get("/api/providers/search/", {"lat": "abc", "lng": "1"}).status_code == 400


# --- Public provider detail -------------------------------------------------

@pytest.mark.django_db
def test_public_detail_shows_active_offerings_only(api, drains):
    haircut = ServiceCategory.objects.create(name="Haircut")
    p = make_provider("p@x.com", "Ravi", 12.98, 77.59)
    add_offering(p, drains, [ServiceMode.ONSITE])
    add_offering(p, haircut, [ServiceMode.CHAT], active=False)

    resp = api.get(f"/api/providers/{p.id}/")  # no auth
    assert resp.status_code == 200
    assert resp.data["full_name"] == "Ravi"
    assert resp.data["location"]["latitude"] == pytest.approx(12.98)
    assert len(resp.data["offerings"]) == 1
    assert resp.data["offerings"][0]["category_name"] == "Drain Cleaning"
