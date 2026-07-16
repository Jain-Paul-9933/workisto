# Workisto

A marketplace connecting customers with individual local service providers
(think Zomato-style *individual* partners, not agencies) — covering both urban
and rural areas, with **paid consultations**, **review-driven dynamic pricing**,
and multiple service **modes** (chat / onsite).

> Portfolio project. Built as a **modular monolith** — deliberately, not a
> microservices sprawl — to demonstrate judgment about matching architecture to
> scale.

## Stack

| Concern | Choice |
|---|---|
| Web / API | Django + Django REST Framework |
| Database | PostgreSQL + **PostGIS** (geospatial provider search) |
| Real-time | Django Channels (WebSockets) over Redis |
| Async jobs | Celery + Redis |
| Payments | Stripe |
| Frontends | Next.js (customer / provider / admin portals — one API) |
| Infra | Docker Compose; deploys to Railway |

## Architecture

One Django project, separated into bounded-context apps:
`accounts`, `catalog`, `providers`, `booking`, `pricing`, `payments`, `chat`,
`reviews`. A separate FastAPI service handles the high-throughput booking-ingest
hot path.

The three "portals" are **three frontends against one role-scoped API**, not
three backends.

## Running it

The only thing you need installed is **Docker Desktop**. GeoDjango's native
libraries (GDAL/GEOS/PROJ) all live inside the container.

```bash
cp .env.example .env      # then edit if you like
docker compose up --build
```

- API health check: http://localhost:8000/health/
- Django admin: http://localhost:8000/admin/

Create an admin user (in a second terminal, once the stack is up):

```bash
docker compose exec web python manage.py createsuperuser
```

## MVP scope

Geo provider search · provider onboarding · paid consultation → estimate →
booking flow · safe slot concurrency (no double-booking) · review-driven dynamic
pricing · Stripe advance + final payment · real-time chat.

## Roadmap (designed, not yet built)

Video call / video messages · multi-service estimates with bundle discounts ·
time-extension / overrun pricing · full availability calendar · admin
customer-service tooling.
