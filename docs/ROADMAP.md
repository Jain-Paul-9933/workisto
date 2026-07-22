# Workisto — Roadmap

Built as a **modular monolith**, one bounded-context Django app at a time. Each
increment is a self-contained, tested vertical slice.

## ✅ Done

| # | Increment | What landed |
|---|---|---|
| 1 | **Foundation** | Docker Compose (PostGIS, Redis, ASGI web via daphne, Celery worker); Channels + Celery wired to Redis; custom `User` (email login, `role`); `/health/`; email-aware admin; DRF configured. |
| 2 | **Domain models — the "nouns"** | `catalog.ServiceCategory`; `providers.ServiceProvider` (PostGIS `PointField`, service radius, denormalised rating); `providers.ServiceOffering` (price lives here, booking type, modes, unique per provider×category); admin + migrations; model tests green on real PostGIS. |
| 3 | **Auth & accounts API** | Session-based register / login / logout / `me`; signup constrained to CUSTOMER/PROVIDER; role permission classes; Redis `cached_db` sessions. See [ADR 0001](adr/0001-auth.md). |

## 🔜 Planned

**First demoable vertical slice** = register a provider → onboard with a map
location → search finds them by distance & rating (increments 3–5).

| # | Increment | Scope |
|---|---|---|
| 4 | **Provider onboarding + catalog API** | Public `ServiceCategory` read; provider self-CRUD of own profile (drops location pin); `ServiceOffering` CRUD; `current_price`/`rating_*` read-only over the API (engine-owned). |
| 5 | **Geo provider search** *(headline)* | Public search: `ST_DWithin` radius filter, distance annotation, ranked by rating. Later becomes the FastAPI async read service. |
| 6 | **Booking + slot concurrency** | `booking` app; consultation → estimate → booking; `select_for_update` row locking → no double-booking. |
| 7 | **Reviews** | `reviews` app; post-booking reviews update `rating_avg`/`rating_count`. |
| 8 | **Dynamic pricing** | `pricing` app; review-driven recompute of `current_price` via Celery. |
| 9 | **Payments** | `payments` app; Stripe advance + final; consultation fee credited. |
| 10 | **Real-time chat** | `chat` app; Channels WebSocket consumer over Redis (session-cookie auth). |
| 11 | **FastAPI read service** | Extract availability search to the async hot path against the same Postgres; short-lived JWT at the boundary (ADR 0001). |
| — | **Frontends (Track B)** | Three Next.js portals against the one role-scoped API. |
