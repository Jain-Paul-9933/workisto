"""
Seed a demonstrable slice of the marketplace: categories, a handful of providers
across Bengaluru (urban + one rural, to show the geo radius at work), a couple of
customers, and some completed jobs with reviews so ratings — and therefore search
ranking and the dynamic-pricing engine — have real data to chew on.

Idempotent: safe to run repeatedly (everything is get-or-create / guarded), so it
can follow any `docker compose up` without piling up duplicates.

    docker compose run --rm web python manage.py seed_demo
"""

from datetime import timedelta
from decimal import Decimal

from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import User
from booking.models import Booking, BookingStatus
from catalog.models import ServiceCategory
from providers.models import BookingType, ServiceMode, ServiceOffering, ServiceProvider
from reviews.models import Review

DEMO_PASSWORD = "workisto-demo"

CATEGORIES = [
    ("Plumbing", "plumbing"),
    ("Electrical", "electrical"),
    ("Cleaning", "cleaning"),
    ("Carpentry", "carpentry"),
    ("Appliance Repair", "appliance-repair"),
    ("Painting", "painting"),
]

# lat/lng are real Bengaluru neighbourhoods; Suresh sits out near Devanahalli
# with a wide radius to demonstrate rural reach.
PROVIDERS = [
    {
        "email": "ravi.plumber@workisto.demo",
        "name": "Ravi Kumar",
        "bio": "Licensed plumber, 15 years across Bengaluru. Leaks, fittings, water heaters.",
        "lat": 12.9352, "lng": 77.6245, "radius": "8",
        "offerings": [
            {"cat": "plumbing", "base": "500", "type": BookingType.INSTANT,
             "modes": [ServiceMode.ONSITE, ServiceMode.CHAT], "duration": 45},
        ],
    },
    {
        "email": "anita.electric@workisto.demo",
        "name": "Anita Sharma",
        "bio": "Certified electrician. Wiring, fixtures, and appliance faults — safe and tidy.",
        "lat": 12.9719, "lng": 77.6412, "radius": "10",
        "offerings": [
            {"cat": "electrical", "base": "600", "type": BookingType.INSTANT,
             "modes": [ServiceMode.ONSITE], "duration": 60},
            {"cat": "appliance-repair", "base": "800", "type": BookingType.CONSULTATION_REQUIRED,
             "fee": "200", "modes": [ServiceMode.ONSITE, ServiceMode.CHAT], "duration": 90},
        ],
    },
    {
        "email": "iqbal.clean@workisto.demo",
        "name": "Mohammed Iqbal",
        "bio": "Deep-cleaning crew lead. Homes and offices, eco-friendly supplies.",
        "lat": 12.9698, "lng": 77.7500, "radius": "15",
        "offerings": [
            {"cat": "cleaning", "base": "1200", "type": BookingType.INSTANT,
             "modes": [ServiceMode.ONSITE], "duration": 120},
        ],
    },
    {
        "email": "lakshmi.wood@workisto.demo",
        "name": "Lakshmi Rao",
        "bio": "Custom carpentry and furniture repair. Every job starts with a consultation.",
        "lat": 12.9250, "lng": 77.5938, "radius": "12",
        "offerings": [
            {"cat": "carpentry", "base": "1500", "type": BookingType.CONSULTATION_REQUIRED,
             "fee": "300", "modes": [ServiceMode.ONSITE, ServiceMode.CHAT], "duration": 90},
        ],
    },
    {
        "email": "suresh.paint@workisto.demo",
        "name": "Suresh Patil",
        "bio": "Interior and exterior painting. Travels widely — rural jobs welcome.",
        "lat": 13.2000, "lng": 77.7000, "radius": "25",
        "offerings": [
            {"cat": "painting", "base": "3000", "type": BookingType.INSTANT,
             "modes": [ServiceMode.ONSITE], "duration": 240},
        ],
    },
]

CUSTOMERS = [
    {"email": "priya@workisto.demo", "name": "Priya Nair"},
    {"email": "arjun@workisto.demo", "name": "Arjun Menon"},
]

# Completed jobs → reviews, so providers have non-zero ratings (which search ranks
# by, and which nudge the dynamic-pricing engine).
ACTIVITY = [
    {"customer": "priya@workisto.demo", "provider": "ravi.plumber@workisto.demo",
     "cat": "plumbing", "rating": 5, "comment": "Fixed a bad leak in 30 minutes. Highly recommend."},
    {"customer": "arjun@workisto.demo", "provider": "anita.electric@workisto.demo",
     "cat": "electrical", "rating": 4, "comment": "Prompt and professional, sorted the wiring."},
    {"customer": "priya@workisto.demo", "provider": "iqbal.clean@workisto.demo",
     "cat": "cleaning", "rating": 5, "comment": "Spotless. The team was thorough and on time."},
    {"customer": "arjun@workisto.demo", "provider": "ravi.plumber@workisto.demo",
     "cat": "plumbing", "rating": 4, "comment": "Good work on the water heater."},
]


class Command(BaseCommand):
    help = "Seed demo data (categories, providers, customers, completed jobs + reviews)."

    def handle(self, *args, **options):
        with transaction.atomic():
            categories = self._categories()
            providers = self._providers(categories)
            customers = self._customers()
            reviews = self._activity(providers, customers)

        self.stdout.write(self.style.SUCCESS("\nDemo data ready."))
        self.stdout.write(
            f"  categories: {len(categories)}  providers: {len(providers)}  "
            f"customers: {len(customers)}  new reviews: {reviews}"
        )
        self.stdout.write("\nSign in at http://localhost:3000 — password for every demo account:")
        self.stdout.write(self.style.WARNING(f"  {DEMO_PASSWORD}"))
        self.stdout.write("  Providers: " + ", ".join(p["email"] for p in PROVIDERS))
        self.stdout.write("  Customers: " + ", ".join(c["email"] for c in CUSTOMERS))
        self.stdout.write(
            "\nTry searching near lat 12.97, lng 77.62 (central Bengaluru) with a 15 km radius."
        )

    # --- steps --------------------------------------------------------------

    def _categories(self):
        result = {}
        for name, slug in CATEGORIES:
            category, _ = ServiceCategory.objects.get_or_create(
                slug=slug, defaults={"name": name, "is_active": True},
            )
            result[slug] = category
        return result

    def _user(self, email, name, role):
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            first, _, last = name.partition(" ")
            return User.objects.create_user(
                email=email, password=DEMO_PASSWORD, role=role,
                first_name=first, last_name=last,
            )

    def _providers(self, categories):
        result = {}
        for spec in PROVIDERS:
            user = self._user(spec["email"], spec["name"], User.Role.PROVIDER)
            provider, _ = ServiceProvider.objects.get_or_create(
                user=user,
                defaults={
                    "full_name": spec["name"],
                    "bio": spec["bio"],
                    "location": Point(spec["lng"], spec["lat"], srid=4326),
                    "service_radius_km": Decimal(spec["radius"]),
                    "accepting_bookings": True,
                },
            )
            for off in spec["offerings"]:
                ServiceOffering.objects.get_or_create(
                    provider=provider,
                    category=categories[off["cat"]],
                    defaults={
                        "base_price": Decimal(off["base"]),
                        "booking_type": off["type"],
                        "consultation_fee": Decimal(off.get("fee", "0")),
                        "supported_modes": list(off["modes"]),
                        "duration_minutes": off["duration"],
                    },
                )
            result[spec["email"]] = provider
        return result

    def _customers(self):
        return {
            spec["email"]: self._user(spec["email"], spec["name"], User.Role.CUSTOMER)
            for spec in CUSTOMERS
        }

    def _activity(self, providers, customers):
        created = 0
        for item in ACTIVITY:
            provider = providers[item["provider"]]
            customer = customers[item["customer"]]
            offering = provider.offerings.filter(category__slug=item["cat"]).first()
            if offering is None:
                continue
            # Idempotency: one seeded review per (customer, provider) pairing.
            if Review.objects.filter(customer=customer, provider=provider).exists():
                continue

            start = timezone.now() - timedelta(days=7)
            booking = Booking.objects.create(
                customer=customer,
                provider=provider,
                offering=offering,
                mode=offering.supported_modes[0],
                status=BookingStatus.COMPLETED,
                start_at=start,
                end_at=start + timedelta(minutes=offering.duration_minutes),
                price=offering.current_price,
                consultation_fee=offering.consultation_fee,
                notes="Seeded completed job (demo).",
            )
            # The post-save signal recomputes the provider's rating aggregate.
            Review.objects.create(
                booking=booking, provider=provider, customer=customer,
                rating=item["rating"], comment=item["comment"],
            )
            created += 1
        return created
