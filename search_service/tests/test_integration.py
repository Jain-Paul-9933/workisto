"""
End-to-end across the service boundary: Django signs a short-lived token, the
FastAPI service verifies it and answers a geo query from the SAME Postgres.

Runs with transaction=True so the rows Django creates are committed and visible
to the FastAPI service's own asyncpg connection. We point that connection at
pytest-django's test database.
"""

import os

import pytest
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.db import connection
from fastapi.testclient import TestClient
from rest_framework.test import APIClient

from catalog.models import ServiceCategory
from providers.models import ServiceMode, ServiceOffering, ServiceProvider

User = get_user_model()

CUSTOMER_LAT, CUSTOMER_LNG = 12.9716, 77.5946


def _test_db_dsn():
    d = connection.settings_dict
    return (
        f"postgresql://{d['USER']}:{d['PASSWORD']}@"
        f"{d['HOST']}:{d['PORT']}/{d['NAME']}"
    )


def make_provider(email, name, lat, lng, rating, category):
    user = User.objects.create_user(email=email, password="pw", role=User.Role.PROVIDER)
    provider = ServiceProvider.objects.create(
        user=user, full_name=name, location=Point(lng, lat, srid=4326),
        rating_avg=rating, rating_count=5,
    )
    ServiceOffering.objects.create(
        provider=provider, category=category, base_price="500.00",
        supported_modes=[ServiceMode.ONSITE],
    )
    return provider


def get_search_token():
    api = APIClient()
    api.force_authenticate(
        User.objects.create_user(email="c@x.com", password="pw",
                                 role=User.Role.CUSTOMER)
    )
    return api.get("/api/auth/search-token/").data["token"]


@pytest.mark.django_db(transaction=True)
def test_end_to_end_geo_search_across_the_boundary():
    category = ServiceCategory.objects.create(name="Drain Cleaning")
    make_provider("hi@x.com", "NearHigh", 12.98, 77.59, "4.50", category)   # ~1 km
    make_provider("lo@x.com", "NearLow", 12.975, 77.594, "3.00", category)  # closer
    make_provider("far@x.com", "Far", 13.60, 77.59, "5.00", category)       # ~70 km

    token = get_search_token()
    os.environ["SEARCH_DATABASE_URL"] = _test_db_dsn()
    try:
        from search_service.main import app

        with TestClient(app) as client:
            resp = client.get(
                "/search/providers",
                params={"lat": CUSTOMER_LAT, "lng": CUSTOMER_LNG,
                        "category": "drain-cleaning", "radius_km": 10},
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 200
            data = resp.json()
            # Far provider excluded despite the best rating; near ones ranked by
            # rating, then proximity.
            assert [r["full_name"] for r in data["results"]] == ["NearHigh", "NearLow"]
            assert data["results"][0]["distance_km"] < 5

            # No token and tampered token are both rejected at the boundary.
            assert client.get(
                "/search/providers",
                params={"lat": CUSTOMER_LAT, "lng": CUSTOMER_LNG},
            ).status_code == 401
            assert client.get(
                "/search/providers",
                params={"lat": CUSTOMER_LAT, "lng": CUSTOMER_LNG},
                headers={"Authorization": "Bearer not.a.real.token"},
            ).status_code == 401
    finally:
        os.environ.pop("SEARCH_DATABASE_URL", None)


@pytest.mark.django_db
def test_token_endpoint_requires_auth():
    api = APIClient()
    assert api.get("/api/auth/search-token/").status_code == 403  # anonymous
