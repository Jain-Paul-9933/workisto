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
| 8 | **Dynamic pricing** | `pricing` app; a bounded, review-driven multiplier moves each offering's `current_price` off `base_price` (min-reviews gate, neutral 3.0, clamped 0.85–1.25). Runs on the **Celery** worker: a review change enqueues the re-price via `transaction.on_commit` so the worker reads the committed rating. `PriceChange` audit trail + provider price-history endpoint. |
| 9 | **Payments** | `payments` app; Stripe **PaymentIntents behind a gateway abstraction** (real `StripeGateway` + `FakeGateway` so tests never touch the network). `Payment` per booking with kinds CONSULTATION/ADVANCE/FINAL, server-authoritative amounts (30% advance, consultation fee credited into the final), partial-unique one-success-per-kind. Confirmation via a **signature-verified, idempotent webhook** — status flips only on Stripe's word, never the client's. |
| 10 | **Real-time chat** | `chat` app; Channels `AsyncWebsocketConsumer` at `ws/bookings/{id}/chat/`, **authenticated by the session cookie** (ADR 0001) and gated to the booking's two participants. Messages persisted + fanned out to a per-booking group over the Redis channel layer; REST history endpoint. Tested with `WebsocketCommunicator` (two clients exchanging live). Wires the `websocket` branch of `config/asgi.py`. |
| 11 | **FastAPI read service** | Separate async `search_service/` (own container/uvicorn, **no Django import**) serving the provider-search hot path over `asyncpg` against the **same** Postgres — raw PostGIS SQL, no second ORM. Trusts a **short-lived HS256 token Django mints** and it verifies statelessly (ADR 0001). Tested end-to-end: Django signs → FastAPI verifies → shared-DB geo results. |

## ✅ Backend complete

All eleven backend increments are built, tested (85 passing on PostGIS + Redis),
and each shipped on its own branch. The first demoable vertical slice
(increments 3–5) works: register a provider → onboard with a map location →
found by distance & rating.

## 🔜 Planned

| # | Increment | Scope |
|---|---|---|
| — | **Frontends (Track B)** | Three Next.js portals (customer / provider / admin) against the one role-scoped API. |
