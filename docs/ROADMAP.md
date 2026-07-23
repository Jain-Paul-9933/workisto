# Workisto — Roadmap

Built as a **modular monolith**, one bounded-context Django app at a time. Each
increment is a self-contained, tested vertical slice.

## ✅ Done

| # | Increment | What landed |
|---|---|---|
| 1 | **Foundation** | Docker Compose (PostGIS, Redis, ASGI web via daphne, Celery worker); Channels + Celery wired to Redis; custom `User` (email login, `role`); `/health/`; email-aware admin; DRF configured. |
| 2 | **Domain models — the "nouns"** | `catalog.ServiceCategory`; `providers.ServiceProvider` (PostGIS `PointField`, service radius, denormalised rating); `providers.ServiceOffering` (price lives here, booking type, modes, unique per provider×category); admin + migrations; model tests green on real PostGIS. |
| 3 | **Auth & accounts API** | Session-based register / login / logout / `me`; signup constrained to CUSTOMER/PROVIDER; role permission classes; Redis `cached_db` sessions. See [ADR 0001](adr/0001-auth.md). |
| 4 | **Provider onboarding + catalog API** | Public `ServiceCategory` read (list + by-slug); provider self-service `POST /providers/` (explicit onboarding, once, lat/lng→PostGIS point), `GET/PATCH /providers/me/`, and own-offering CRUD under `/providers/me/offerings/`. Queryset scoped to caller = object-level isolation; `current_price`/`rating_*` read-only (engine-owned); category immutable after create. |
| 5 | **Geo provider search** *(headline)* | Public `GET /providers/search/`: `ST_DWithin` radius filter (GiST-indexed) around lat/lng, category + mode filters that must match a **single** offering, distance annotated in, ranked by rating then proximity. Plus public `GET /providers/{id}/` detail with active offerings. Excludes paused/offering-less providers. Later becomes the FastAPI async read service. |
| 6 | **Booking + slot concurrency** | `booking` app; instant bookings and the consultation→estimate→confirm flow over one `Booking` row; slot reservation guarded by a `select_for_update` lock on the provider row (no double-booking, proven by a real 2-thread test). Participant-scoped visibility; cancel frees the slot. See [ADR 0002](adr/0002-slot-concurrency.md). |
| 7 | **Reviews** | `reviews` app; a customer reviews their own **completed** booking (one review per booking); a signal recomputes the provider's denormalised `rating_avg`/`rating_count` on every review change — the values search ranks by. Public per-provider review list; owner-only edit/delete. Added a provider `complete` action to bookings to gate reviews. |

## 🔜 Planned

**First demoable vertical slice complete** (increments 3–5): register a provider
→ onboard with a map location → search finds them by distance & rating. ✅

| # | Increment | Scope |
|---|---|---|
| 8 | **Dynamic pricing** | `pricing` app; review-driven recompute of `current_price` via Celery. |
| 9 | **Payments** | `payments` app; Stripe advance + final; consultation fee credited. |
| 10 | **Real-time chat** | `chat` app; Channels WebSocket consumer over Redis (session-cookie auth). |
| 11 | **FastAPI read service** | Extract availability search to the async hot path against the same Postgres; short-lived JWT at the boundary (ADR 0001). |
| — | **Frontends (Track B)** | Three Next.js portals against the one role-scoped API. |
