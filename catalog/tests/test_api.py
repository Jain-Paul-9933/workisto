import pytest
from rest_framework.test import APIClient

from catalog.models import ServiceCategory


@pytest.fixture
def api():
    return APIClient()


@pytest.mark.django_db
def test_category_list_is_public_and_hides_inactive(api):
    ServiceCategory.objects.create(name="Drain Cleaning")
    ServiceCategory.objects.create(name="Retired Service", is_active=False)

    resp = api.get("/api/categories/")  # no auth
    assert resp.status_code == 200
    names = [c["name"] for c in resp.data]
    assert "Drain Cleaning" in names
    assert "Retired Service" not in names


@pytest.mark.django_db
def test_category_detail_by_slug(api):
    ServiceCategory.objects.create(name="AC Repair")

    resp = api.get("/api/categories/ac-repair/")
    assert resp.status_code == 200
    assert resp.data["name"] == "AC Repair"
    assert resp.data["default_duration_minutes"] == 30
