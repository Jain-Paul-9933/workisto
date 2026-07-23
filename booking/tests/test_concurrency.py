"""
The one test that proves the double-booking guarantee, not just asserts it.

Two customers race for the exact same slot from separate threads (each with its
own DB connection, real commits — hence transaction=True). Without the
provider-row lock in services._lock_provider_and_check, both would see an empty
calendar and both would insert. With it, they serialize: exactly one CONFIRMED
booking survives.
"""

import threading
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.db import connections
from django.utils import timezone

from booking.models import Booking, BookingStatus
from booking.services import SlotUnavailable, create_instant_booking
from catalog.models import ServiceCategory
from providers.models import BookingType, ServiceMode, ServiceOffering, ServiceProvider

User = get_user_model()


@pytest.mark.django_db(transaction=True)
def test_concurrent_bookings_for_one_slot_yield_exactly_one():
    category = ServiceCategory.objects.create(name="Drain Cleaning")
    puser = User.objects.create_user(
        email="prov@x.com", password="pw", role=User.Role.PROVIDER,
    )
    provider = ServiceProvider.objects.create(user=puser, full_name="Ravi")
    offering = ServiceOffering.objects.create(
        provider=provider, category=category, base_price="500.00",
        supported_modes=[ServiceMode.ONSITE], booking_type=BookingType.INSTANT,
    )
    c1 = User.objects.create_user(email="c1@x.com", password="pw", role=User.Role.CUSTOMER)
    c2 = User.objects.create_user(email="c2@x.com", password="pw", role=User.Role.CUSTOMER)
    slot = timezone.now() + timedelta(days=1)

    results = {}
    start = threading.Barrier(2)  # release both threads at the same instant

    def attempt(key, customer_id):
        start.wait()
        try:
            create_instant_booking(
                customer=User.objects.get(pk=customer_id),
                offering=ServiceOffering.objects.get(pk=offering.id),
                mode=ServiceMode.ONSITE,
                start_at=slot,
            )
            results[key] = "ok"
        except SlotUnavailable:
            results[key] = "conflict"
        finally:
            connections.close_all()  # thread-local; don't leak the connection

    threads = [
        threading.Thread(target=attempt, args=("a", c1.id)),
        threading.Thread(target=attempt, args=("b", c2.id)),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert sorted(results.values()) == ["conflict", "ok"]
    assert Booking.objects.filter(status=BookingStatus.CONFIRMED).count() == 1
