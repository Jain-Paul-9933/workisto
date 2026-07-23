from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from booking.models import Booking, BookingStatus
from catalog.models import ServiceCategory
from providers.models import ServiceMode, ServiceOffering, ServiceProvider
from reviews.models import Review

User = get_user_model()


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
def offering(provider):
    return ServiceOffering.objects.create(
        provider=provider, category=ServiceCategory.objects.create(name="Haircut"),
        base_price="300.00", supported_modes=[ServiceMode.ONSITE],
    )


def make_customer(email, first_name=""):
    return User.objects.create_user(
        email=email, password="s3cret-pass-123", role=User.Role.CUSTOMER,
        first_name=first_name,
    )


def completed_booking(customer, offering):
    start = timezone.now() - timedelta(days=1)
    return Booking.objects.create(
        customer=customer, provider=offering.provider, offering=offering,
        mode=ServiceMode.ONSITE, status=BookingStatus.COMPLETED,
        start_at=start, end_at=start + timedelta(minutes=30), price="300.00",
    )


# --- Rating aggregation -----------------------------------------------------

@pytest.mark.django_db
def test_review_rolls_up_to_provider_rating(api, provider, offering):
    customer = make_customer("c1@x.com")
    booking = completed_booking(customer, offering)
    api.force_authenticate(customer)

    resp = api.post("/api/reviews/", {"booking": booking.id, "rating": 5,
                                      "comment": "Great"}, format="json")
    assert resp.status_code == 201

    provider.refresh_from_db()
    assert provider.rating_avg == pytest.approx(5.00) or str(provider.rating_avg) == "5.00"
    assert provider.rating_count == 1


@pytest.mark.django_db
def test_second_review_averages(api, provider, offering):
    c1, c2 = make_customer("c1@x.com"), make_customer("c2@x.com")
    b1, b2 = completed_booking(c1, offering), completed_booking(c2, offering)

    api.force_authenticate(c1)
    api.post("/api/reviews/", {"booking": b1.id, "rating": 5}, format="json")
    api.force_authenticate(c2)
    api.post("/api/reviews/", {"booking": b2.id, "rating": 3}, format="json")

    provider.refresh_from_db()
    assert str(provider.rating_avg) == "4.00"
    assert provider.rating_count == 2


@pytest.mark.django_db
def test_update_review_recomputes(api, provider, offering):
    customer = make_customer("c1@x.com")
    booking = completed_booking(customer, offering)
    api.force_authenticate(customer)
    review = api.post("/api/reviews/", {"booking": booking.id, "rating": 5},
                      format="json").data

    api.patch(f"/api/reviews/{review['id']}/", {"rating": 1}, format="json")

    provider.refresh_from_db()
    assert str(provider.rating_avg) == "1.00"
    assert provider.rating_count == 1


@pytest.mark.django_db
def test_delete_review_resets_when_last(api, provider, offering):
    customer = make_customer("c1@x.com")
    booking = completed_booking(customer, offering)
    api.force_authenticate(customer)
    review = api.post("/api/reviews/", {"booking": booking.id, "rating": 4},
                      format="json").data

    assert api.delete(f"/api/reviews/{review['id']}/").status_code == 204

    provider.refresh_from_db()
    assert str(provider.rating_avg) == "0.00"
    assert provider.rating_count == 0


# --- Guards -----------------------------------------------------------------

@pytest.mark.django_db
def test_cannot_review_uncompleted_booking(api, provider, offering):
    customer = make_customer("c1@x.com")
    booking = Booking.objects.create(
        customer=customer, provider=provider, offering=offering,
        mode=ServiceMode.ONSITE, status=BookingStatus.CONFIRMED,
        start_at=timezone.now() + timedelta(days=1),
        end_at=timezone.now() + timedelta(days=1, minutes=30),
    )
    api.force_authenticate(customer)
    resp = api.post("/api/reviews/", {"booking": booking.id, "rating": 5}, format="json")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_cannot_review_someone_elses_booking(api, offering):
    owner = make_customer("owner@x.com")
    booking = completed_booking(owner, offering)
    intruder = make_customer("intruder@x.com")
    api.force_authenticate(intruder)
    resp = api.post("/api/reviews/", {"booking": booking.id, "rating": 5}, format="json")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_cannot_review_twice(api, offering):
    customer = make_customer("c1@x.com")
    booking = completed_booking(customer, offering)
    api.force_authenticate(customer)
    assert api.post("/api/reviews/", {"booking": booking.id, "rating": 5},
                    format="json").status_code == 201
    assert api.post("/api/reviews/", {"booking": booking.id, "rating": 4},
                    format="json").status_code == 400


@pytest.mark.django_db
@pytest.mark.parametrize("bad", [0, 6])
def test_rating_out_of_range_rejected(api, offering, bad):
    customer = make_customer("c1@x.com")
    booking = completed_booking(customer, offering)
    api.force_authenticate(customer)
    resp = api.post("/api/reviews/", {"booking": booking.id, "rating": bad}, format="json")
    assert resp.status_code == 400


# --- Public listing ---------------------------------------------------------

@pytest.mark.django_db
def test_public_provider_reviews_list(api, provider, offering):
    customer = make_customer("c1@x.com", first_name="Asha")
    booking = completed_booking(customer, offering)
    api.force_authenticate(customer)
    api.post("/api/reviews/", {"booking": booking.id, "rating": 5, "comment": "Ace"},
             format="json")

    api.force_authenticate(user=None)  # anonymous
    resp = api.get(f"/api/providers/{provider.id}/reviews/")
    assert resp.status_code == 200
    assert len(resp.data) == 1
    assert resp.data[0]["reviewer"] == "Asha"      # display name, not email
    assert resp.data[0]["comment"] == "Ace"


# --- Completion gate --------------------------------------------------------

@pytest.mark.django_db
def test_only_provider_can_complete(api, provider, offering):
    customer = make_customer("c1@x.com")
    booking = Booking.objects.create(
        customer=customer, provider=provider, offering=offering,
        mode=ServiceMode.ONSITE, status=BookingStatus.CONFIRMED,
        start_at=timezone.now() + timedelta(days=1),
        end_at=timezone.now() + timedelta(days=1, minutes=30),
    )
    api.force_authenticate(customer)
    assert api.post(f"/api/bookings/{booking.id}/complete/").status_code == 403

    api.force_authenticate(provider.user)
    resp = api.post(f"/api/bookings/{booking.id}/complete/")
    assert resp.status_code == 200
    assert resp.data["status"] == BookingStatus.COMPLETED
