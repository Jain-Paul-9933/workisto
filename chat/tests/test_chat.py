from datetime import timedelta

import pytest
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from rest_framework.test import APIClient

from booking.models import Booking, BookingStatus
from catalog.models import ServiceCategory
from chat.consumers import ChatConsumer
from chat.models import ChatMessage
from providers.models import ServiceMode, ServiceOffering, ServiceProvider

User = get_user_model()


@database_sync_to_async
def make_world():
    puser = User.objects.create_user(
        email="prov@x.com", password="pw", role=User.Role.PROVIDER,
    )
    provider = ServiceProvider.objects.create(user=puser, full_name="Ravi")
    offering = ServiceOffering.objects.create(
        provider=provider, category=ServiceCategory.objects.create(name="Haircut"),
        base_price="300.00", supported_modes=[ServiceMode.ONSITE],
    )
    customer = User.objects.create_user(
        email="cust@x.com", password="pw", role=User.Role.CUSTOMER,
    )
    outsider = User.objects.create_user(
        email="out@x.com", password="pw", role=User.Role.CUSTOMER,
    )
    start = timezone.now() + timedelta(days=1)
    booking = Booking.objects.create(
        customer=customer, provider=provider, offering=offering,
        mode=ServiceMode.ONSITE, status=BookingStatus.CONFIRMED,
        start_at=start, end_at=start + timedelta(minutes=30), price="300.00",
    )
    return {"booking": booking, "customer": customer,
            "provider_user": puser, "outsider": outsider}


def connect_as(user, booking_id):
    # Drive the consumer directly, injecting the scope the AuthMiddlewareStack
    # and URLRouter would set in production.
    comm = WebsocketCommunicator(
        ChatConsumer.as_asgi(), f"/ws/bookings/{booking_id}/chat/",
    )
    comm.scope["user"] = user
    comm.scope["url_route"] = {"kwargs": {"booking_id": str(booking_id)}}
    return comm


@pytest.mark.django_db(transaction=True)
async def test_participants_exchange_messages_live():
    world = await make_world()
    booking = world["booking"]

    cust = connect_as(world["customer"], booking.id)
    prov = connect_as(world["provider_user"], booking.id)
    assert (await cust.connect())[0] is True
    assert (await prov.connect())[0] is True

    await cust.send_json_to({"message": "Hi, are you free tomorrow?"})

    # Both ends receive the server's authoritative copy (id + timestamp).
    for comm in (cust, prov):
        event = await comm.receive_json_from(timeout=2)
        assert event["message"] == "Hi, are you free tomorrow?"
        assert event["sender"] == "cust@x.com"
        assert "id" in event and "created_at" in event

    persisted = await database_sync_to_async(
        ChatMessage.objects.filter(booking=booking).count
    )()
    assert persisted == 1

    await cust.disconnect()
    await prov.disconnect()


@pytest.mark.django_db(transaction=True)
async def test_anonymous_is_rejected():
    world = await make_world()
    comm = connect_as(AnonymousUser(), world["booking"].id)
    connected, code = await comm.connect()
    assert connected is False
    assert code == 4401


@pytest.mark.django_db(transaction=True)
async def test_non_participant_is_rejected():
    world = await make_world()
    comm = connect_as(world["outsider"], world["booking"].id)
    connected, code = await comm.connect()
    assert connected is False
    assert code == 4403


@pytest.mark.django_db(transaction=True)
async def test_blank_message_is_ignored():
    world = await make_world()
    comm = connect_as(world["customer"], world["booking"].id)
    await comm.connect()

    await comm.send_json_to({"message": "   "})
    assert await comm.receive_nothing(timeout=0.5) is True   # nothing broadcast
    count = await database_sync_to_async(ChatMessage.objects.count)()
    assert count == 0

    await comm.disconnect()


# --- REST history -----------------------------------------------------------

@pytest.mark.django_db
def test_message_history_is_participant_scoped():
    puser = User.objects.create_user(
        email="prov@x.com", password="pw", role=User.Role.PROVIDER,
    )
    provider = ServiceProvider.objects.create(user=puser, full_name="Ravi")
    offering = ServiceOffering.objects.create(
        provider=provider, category=ServiceCategory.objects.create(name="Haircut"),
        base_price="300.00", supported_modes=[ServiceMode.ONSITE],
    )
    customer = User.objects.create_user(
        email="cust@x.com", password="pw", role=User.Role.CUSTOMER,
    )
    start = timezone.now() + timedelta(days=1)
    booking = Booking.objects.create(
        customer=customer, provider=provider, offering=offering,
        mode=ServiceMode.ONSITE, status=BookingStatus.CONFIRMED,
        start_at=start, end_at=start + timedelta(minutes=30), price="300.00",
    )
    ChatMessage.objects.create(booking=booking, sender=customer, body="Hello")

    api = APIClient()
    api.force_authenticate(customer)
    resp = api.get(f"/api/bookings/{booking.id}/messages/")
    assert resp.status_code == 200
    assert len(resp.data) == 1
    assert resp.data[0]["body"] == "Hello"

    outsider = User.objects.create_user(
        email="out@x.com", password="pw", role=User.Role.CUSTOMER,
    )
    api.force_authenticate(outsider)
    assert api.get(f"/api/bookings/{booking.id}/messages/").status_code == 404
