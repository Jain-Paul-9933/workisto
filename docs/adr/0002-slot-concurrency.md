# ADR 0002 — No double-booking: lock the provider row

- **Status:** Accepted (2026-07)
- **Context increment:** 6 (Booking + slot concurrency)

## Context

Two customers can race for the same provider's time slot. The obvious "check for
an overlap, then insert" is **not** safe under concurrency: both transactions
run the overlap query, both see an empty window, and both insert. Locking the
*existing* bookings with `SELECT ... FOR UPDATE` doesn't rescue it either —
there are no rows yet to lock (a phantom).

## Decision

Serialize slot reservation **per provider** by locking the provider row
(`ServiceProvider.objects.select_for_update().get(...)`) at the top of the
reservation transaction, *before* the overlap check. Racers for the same
provider block on that single row, so exactly one proceeds at a time; the loser
sees the now-committed booking and is rejected with a `409`.

## Why this works, and the trade-offs

- **Correct:** the racers contend on a row that always exists (the provider),
  which closes the phantom gap that locking not-yet-existing bookings leaves.
- **Cheap:** contention is scoped to one provider, and a provider books one job
  at a time — no global bottleneck.
- **Clean UX:** an application-level check returns `409 SlotUnavailable`, not a
  raw database `IntegrityError`.

## Considered / deferred

A Postgres `EXCLUDE USING gist` constraint over
`(provider WITH =, tstzrange(start_at, end_at) WITH &&) WHERE status = CONFIRMED`
would enforce non-overlap at the **storage layer**, independent of application
code — the strongest possible guarantee. Deferred to keep this increment focused
(it needs the `btree_gist` extension and an expression-index migration); the
row lock already prevents double-booking today, and the constraint slots in
later as defense-in-depth.

Proven, not just asserted: `booking/tests/test_concurrency.py` fires two real
threads (own connections, real commits) at one slot and asserts exactly one
`CONFIRMED` booking survives.
