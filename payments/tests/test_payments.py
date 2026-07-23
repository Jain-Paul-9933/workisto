import json
from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from booking.models import Booking, BookingStatus
from catalog.models import ServiceCategory
from payments.models import Payment, PaymentKind, PaymentStatus
from payments.services import amount_for
from providers.models import ServiceMode, ServiceOffering, ServiceProvider

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
def customer(db):
    return User.objects.create_user(
        email="cust@x.com", password="s3cret-pass-123", role=User.Role.CUSTOMER,
    )


@pytest.fixture
def offering(provider):
    return ServiceOffering.objects.create(
        provider=provider, category=ServiceCategory.objects.create(name="Kitchen"),
        base_price="1000.00", consultation_fee="200.00",
        supported_modes=[ServiceMode.ONSITE],
    )


def make_booking(customer, offering, *, price="1000.00", consultation_fee="200.00"):
    start = timezone.now() + timedelta(days=1)
    booking = Booking.objects.create(
        customer=customer, provider=offering.provider, offering=offering,
        mode=ServiceMode.ONSITE, status=BookingStatus.CONFIRMED,
        start_at=start, end_at=start + timedelta(minutes=30),
        price=price, consultation_fee=consultation_fee,
    )
    booking.refresh_from_db()  # coerce the money fields back to Decimal
    return booking


def webhook_body(intent_id, type_="payment_intent.succeeded"):
    return json.dumps({"type": type_, "data": {"object": {"id": intent_id}}})


# --- Amount math ------------------------------------------------------------

@pytest.mark.django_db
def test_amount_math(customer, offering):
    booking = make_booking(customer, offering)  # price 1000, consult fee 200
    assert amount_for(booking, PaymentKind.CONSULTATION) == Decimal("200.00")
    assert amount_for(booking, PaymentKind.ADVANCE) == Decimal("300.00")   # 30%
    # No consultation paid yet → no credit.
    assert amount_for(booking, PaymentKind.FINAL) == Decimal("700.00")


@pytest.mark.django_db
def test_consultation_fee_credited_into_final(customer, offering):
    booking = make_booking(customer, offering)
    # A settled consultation payment exists...
    Payment.objects.create(
        booking=booking, kind=PaymentKind.CONSULTATION, amount="200.00",
        status=PaymentStatus.SUCCEEDED,
    )
    # ...so the final is 1000 - 300 advance - 200 credit = 500.
    assert amount_for(booking, PaymentKind.FINAL) == Decimal("500.00")


# --- Creating a payment -----------------------------------------------------

@pytest.mark.django_db
def test_pay_creates_pending_intent(api, customer, offering):
    booking = make_booking(customer, offering)
    api.force_authenticate(customer)

    resp = api.post(f"/api/bookings/{booking.id}/pay/",
                    {"kind": PaymentKind.ADVANCE}, format="json")

    assert resp.status_code == 201
    assert resp.data["status"] == PaymentStatus.PENDING
    assert resp.data["amount"] == "300.00"
    assert resp.data["client_secret"]                    # handed to the client
    payment = Payment.objects.get(id=resp.data["id"])
    assert payment.external_id == f"pi_fake_{payment.id}"  # from the gateway


@pytest.mark.django_db
def test_only_customer_can_pay(api, provider, customer, offering):
    booking = make_booking(customer, offering)
    api.force_authenticate(provider.user)
    resp = api.post(f"/api/bookings/{booking.id}/pay/",
                    {"kind": PaymentKind.ADVANCE}, format="json")
    assert resp.status_code == 403


# --- Webhook confirmation ---------------------------------------------------

@pytest.mark.django_db
def test_webhook_marks_succeeded_and_is_idempotent(api, customer, offering):
    booking = make_booking(customer, offering)
    api.force_authenticate(customer)
    payment_id = api.post(f"/api/bookings/{booking.id}/pay/",
                          {"kind": PaymentKind.ADVANCE}, format="json").data["id"]
    payment = Payment.objects.get(id=payment_id)

    api.force_authenticate(user=None)  # Stripe is unauthenticated
    body = webhook_body(payment.external_id)
    for _ in range(2):  # deliver twice — must be idempotent
        resp = api.post("/api/payments/webhook/", data=body,
                        content_type="application/json", HTTP_STRIPE_SIGNATURE="sig_ok")
        assert resp.status_code == 200

    payment.refresh_from_db()
    assert payment.status == PaymentStatus.SUCCEEDED
    assert Payment.objects.filter(
        booking=booking, kind=PaymentKind.ADVANCE, status=PaymentStatus.SUCCEEDED,
    ).count() == 1


@pytest.mark.django_db
def test_webhook_bad_signature_rejected(api, customer, offering):
    booking = make_booking(customer, offering)
    api.force_authenticate(customer)
    payment_id = api.post(f"/api/bookings/{booking.id}/pay/",
                          {"kind": PaymentKind.ADVANCE}, format="json").data["id"]
    payment = Payment.objects.get(id=payment_id)

    api.force_authenticate(user=None)
    resp = api.post("/api/payments/webhook/", data=webhook_body(payment.external_id),
                    content_type="application/json", HTTP_STRIPE_SIGNATURE="bad")
    assert resp.status_code == 400
    payment.refresh_from_db()
    assert payment.status == PaymentStatus.PENDING   # untouched


@pytest.mark.django_db
def test_webhook_failure_marks_failed(api, customer, offering):
    booking = make_booking(customer, offering)
    api.force_authenticate(customer)
    payment_id = api.post(f"/api/bookings/{booking.id}/pay/",
                          {"kind": PaymentKind.ADVANCE}, format="json").data["id"]
    payment = Payment.objects.get(id=payment_id)

    api.force_authenticate(user=None)
    resp = api.post(
        "/api/payments/webhook/",
        data=webhook_body(payment.external_id, "payment_intent.payment_failed"),
        content_type="application/json", HTTP_STRIPE_SIGNATURE="sig_ok",
    )
    assert resp.status_code == 200
    payment.refresh_from_db()
    assert payment.status == PaymentStatus.FAILED


@pytest.mark.django_db
def test_cannot_pay_same_kind_twice(api, customer, offering):
    booking = make_booking(customer, offering)
    Payment.objects.create(
        booking=booking, kind=PaymentKind.ADVANCE, amount="300.00",
        status=PaymentStatus.SUCCEEDED,
    )
    api.force_authenticate(customer)
    resp = api.post(f"/api/bookings/{booking.id}/pay/",
                    {"kind": PaymentKind.ADVANCE}, format="json")
    assert resp.status_code == 400


# --- Listing ----------------------------------------------------------------

@pytest.mark.django_db
def test_payments_list_scoped_to_participants(api, customer, offering):
    booking = make_booking(customer, offering)
    Payment.objects.create(booking=booking, kind=PaymentKind.ADVANCE, amount="300.00")

    # Participant sees them.
    api.force_authenticate(customer)
    assert len(api.get(f"/api/bookings/{booking.id}/payments/").data) == 1

    # Outsider can't even resolve the booking.
    outsider = User.objects.create_user(
        email="nosy@x.com", password="s3cret-pass-123", role=User.Role.CUSTOMER,
    )
    api.force_authenticate(outsider)
    assert api.get(f"/api/bookings/{booking.id}/payments/").status_code == 404
