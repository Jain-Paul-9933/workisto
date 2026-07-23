from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from booking.models import Booking, BookingStatus
from catalog.models import ServiceCategory
from providers.models import (
    BookingType,
    ServiceMode,
    ServiceOffering,
    ServiceProvider,
)

User = get_user_model()


def tomorrow():
    return timezone.now() + timedelta(days=1)


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def provider(db):
    user = User.objects.create_user(
        email="ravi@x.com", password="s3cret-pass-123", role=User.Role.PROVIDER,
    )
    return ServiceProvider.objects.create(user=user, full_name="Ravi")


@pytest.fixture
def customer(db):
    return User.objects.create_user(
        email="cust@x.com", password="s3cret-pass-123", role=User.Role.CUSTOMER,
    )


@pytest.fixture
def instant_offering(provider):
    return ServiceOffering.objects.create(
        provider=provider,
        category=ServiceCategory.objects.create(name="Haircut"),
        base_price="300.00", supported_modes=[ServiceMode.ONSITE],
        booking_type=BookingType.INSTANT,
    )


@pytest.fixture
def consult_offering(provider):
    return ServiceOffering.objects.create(
        provider=provider,
        category=ServiceCategory.objects.create(name="Kitchen Remodel"),
        base_price="0.00", consultation_fee="200.00",
        supported_modes=[ServiceMode.ONSITE],
        booking_type=BookingType.CONSULTATION_REQUIRED,
    )


# --- Instant booking --------------------------------------------------------

@pytest.mark.django_db
def test_instant_booking_confirms_with_slot(api, customer, instant_offering):
    api.force_authenticate(customer)
    slot = tomorrow()

    resp = api.post("/api/bookings/", {
        "offering": instant_offering.id, "mode": ServiceMode.ONSITE,
        "start_at": slot.isoformat(),
    }, format="json")

    assert resp.status_code == 201
    assert resp.data["status"] == BookingStatus.CONFIRMED
    assert resp.data["price"] == "300.00"           # snapshot of current_price
    assert resp.data["start_at"] is not None


@pytest.mark.django_db
def test_instant_booking_requires_start_at(api, customer, instant_offering):
    api.force_authenticate(customer)
    resp = api.post("/api/bookings/", {
        "offering": instant_offering.id, "mode": ServiceMode.ONSITE,
    }, format="json")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_unsupported_mode_rejected(api, customer, instant_offering):
    api.force_authenticate(customer)
    resp = api.post("/api/bookings/", {
        "offering": instant_offering.id, "mode": ServiceMode.CHAT,  # onsite only
        "start_at": tomorrow().isoformat(),
    }, format="json")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_provider_cannot_create_booking(api, provider, instant_offering):
    api.force_authenticate(provider.user)
    resp = api.post("/api/bookings/", {
        "offering": instant_offering.id, "mode": ServiceMode.ONSITE,
        "start_at": tomorrow().isoformat(),
    }, format="json")
    assert resp.status_code == 403


# --- Slot safety (single-request semantics) ---------------------------------

@pytest.mark.django_db
def test_overlapping_slot_rejected(api, customer, instant_offering):
    api.force_authenticate(customer)
    slot = tomorrow()
    first = api.post("/api/bookings/", {
        "offering": instant_offering.id, "mode": ServiceMode.ONSITE,
        "start_at": slot.isoformat(),
    }, format="json")
    assert first.status_code == 201

    # 15 min later overlaps the 30-min job that's already booked.
    overlap = api.post("/api/bookings/", {
        "offering": instant_offering.id, "mode": ServiceMode.ONSITE,
        "start_at": (slot + timedelta(minutes=15)).isoformat(),
    }, format="json")
    assert overlap.status_code == 409


@pytest.mark.django_db
def test_adjacent_slot_allowed(api, customer, instant_offering):
    api.force_authenticate(customer)
    slot = tomorrow()
    api.post("/api/bookings/", {
        "offering": instant_offering.id, "mode": ServiceMode.ONSITE,
        "start_at": slot.isoformat(),
    }, format="json")
    # Starts exactly when the first ends → no overlap.
    adjacent = api.post("/api/bookings/", {
        "offering": instant_offering.id, "mode": ServiceMode.ONSITE,
        "start_at": (slot + timedelta(minutes=30)).isoformat(),
    }, format="json")
    assert adjacent.status_code == 201


@pytest.mark.django_db
def test_cancel_frees_the_slot(api, customer, instant_offering):
    api.force_authenticate(customer)
    slot = tomorrow()
    first = api.post("/api/bookings/", {
        "offering": instant_offering.id, "mode": ServiceMode.ONSITE,
        "start_at": slot.isoformat(),
    }, format="json").data

    assert api.post(f"/api/bookings/{first['id']}/cancel/").status_code == 200

    # Same slot is bookable again now that the first is cancelled.
    again = api.post("/api/bookings/", {
        "offering": instant_offering.id, "mode": ServiceMode.ONSITE,
        "start_at": slot.isoformat(),
    }, format="json")
    assert again.status_code == 201


# --- Consultation → estimate → confirm --------------------------------------

@pytest.mark.django_db
def test_consultation_flow(api, customer, provider, consult_offering):
    # 1. Customer files a consultation request — no slot yet.
    api.force_authenticate(customer)
    created = api.post("/api/bookings/", {
        "offering": consult_offering.id, "mode": ServiceMode.ONSITE,
        "notes": "Full kitchen redo",
    }, format="json")
    assert created.status_code == 201
    assert created.data["status"] == BookingStatus.PENDING_ESTIMATE
    assert created.data["consultation_fee"] == "200.00"
    assert created.data["start_at"] is None
    booking_id = created.data["id"]

    # 2. Customer cannot self-estimate.
    assert api.post(f"/api/bookings/{booking_id}/estimate/",
                    {"estimate_amount": "5000.00"}, format="json").status_code == 403

    # 3. Provider quotes.
    api.force_authenticate(provider.user)
    est = api.post(f"/api/bookings/{booking_id}/estimate/",
                   {"estimate_amount": "5000.00"}, format="json")
    assert est.status_code == 200
    assert est.data["status"] == BookingStatus.ESTIMATED

    # 4. Provider cannot confirm on the customer's behalf.
    assert api.post(f"/api/bookings/{booking_id}/confirm/",
                    {"start_at": tomorrow().isoformat()}, format="json").status_code == 403

    # 5. Customer accepts + picks a slot → CONFIRMED, price = estimate.
    api.force_authenticate(customer)
    confirmed = api.post(f"/api/bookings/{booking_id}/confirm/",
                         {"start_at": tomorrow().isoformat()}, format="json")
    assert confirmed.status_code == 200
    assert confirmed.data["status"] == BookingStatus.CONFIRMED
    assert confirmed.data["price"] == "5000.00"


@pytest.mark.django_db
def test_cannot_confirm_before_estimate(api, customer, consult_offering):
    api.force_authenticate(customer)
    created = api.post("/api/bookings/", {
        "offering": consult_offering.id, "mode": ServiceMode.ONSITE,
    }, format="json").data
    resp = api.post(f"/api/bookings/{created['id']}/confirm/",
                    {"start_at": tomorrow().isoformat()}, format="json")
    assert resp.status_code == 400  # still PENDING_ESTIMATE


# --- Visibility -------------------------------------------------------------

@pytest.mark.django_db
def test_outsider_cannot_see_booking(api, customer, instant_offering):
    api.force_authenticate(customer)
    slot = tomorrow()
    booking = api.post("/api/bookings/", {
        "offering": instant_offering.id, "mode": ServiceMode.ONSITE,
        "start_at": slot.isoformat(),
    }, format="json").data

    outsider = User.objects.create_user(
        email="nosy@x.com", password="s3cret-pass-123", role=User.Role.CUSTOMER,
    )
    api.force_authenticate(outsider)
    assert api.get(f"/api/bookings/{booking['id']}/").status_code == 404
