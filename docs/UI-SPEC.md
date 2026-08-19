# Workisto — UI design brief

Paste this into a design tool (claude.ai, v0, Figma AI) to generate screens. It
describes what exists in the codebase today, so anything produced from it can be
wired to the real API rather than redrawn.

---

## 1. The product

**Workisto** is a marketplace connecting customers with individual local service
providers — plumbers, electricians, cleaners, carpenters, painters — across both
**urban and rural India**. Think "Zomato for service partners."

Three things make it different from a generic booking app, and the UI has to
carry all three:

1. **Paid consultations.** Some jobs can't be priced sight-unseen. A customer
   requests a consultation, the provider inspects and quotes an estimate, and
   only then does the customer confirm. The interface must make an *estimate*
   feel different from a *price*.
2. **Review-driven dynamic pricing.** A provider's rating moves their price
   within a bounded band. Prices are not static, so a price is shown as
   "current", never as a permanent fact.
3. **Two service modes.** Work happens **on-site** or **over chat**. The mode
   changes what a booking even means, so it is never buried in fine print.

**Currency: ₹ (INR)** everywhere. Money arrives from the API as a string —
render exactly two decimals.

---

## 2. Design constraints

These are requirements, not preferences.

- **Mobile-first.** Most users are on phones, many on low-end Android with
  patchy connectivity. Design 360px first; desktop is the adaptation.
- **Rural reach.** Assume slow networks. Every screen needs a real loading state
  and a real offline/error state. Avoid heavy imagery.
- **Low literacy tolerance.** Lead with plain words, not jargon. Never make a
  coordinate, an ID, or a status enum the primary thing a user reads.
- **Light and dark.** Both are first-class; the app already ships dark mode.
- **Accessibility.** Minimum 4.5:1 contrast, 44px touch targets, visible focus
  rings, full keyboard navigation. Never encode meaning in color alone — pair
  every status color with a text label.
- **No coordinates in the interface.** Location is chosen by searching a place
  name or tapping a map. Latitude/longitude is a hidden fallback.

---

## 3. Design system

### Tokens needed
- **Color:** primary (currently indigo), plus semantic success / warning /
  danger / info, and a neutral ramp. Each needs a light and dark value.
- **Status tones:** exactly five — `neutral`, `green`, `amber`, `red`, `indigo`.
  Every badge in the app maps to one of these.
- **Type scale:** page title, section heading, body, small, caption. One family.
- **Spacing scale, radius scale, one elevation/shadow step.**

### Component inventory (already exists in code — redesign, don't reinvent)
`Button` (primary/secondary/danger, loading + disabled) · `Input` · `Select` ·
`Textarea` · `Field` (label + control + error) · `Card` · `Badge` (5 tones) ·
`ErrorText` · nav chrome (brand, section links, sign out)

### Components that need real design attention
- **MapPicker** — place-search box with dropdown results, map, draggable pin,
  and a human-readable "Selected: …" label underneath.
- **ChatBox** — live message bubbles, own vs. other, timestamps, connection
  state.
- **PaymentsPanel** — a payment breakdown people trust at a glance.

---

## 4. Screens

Twelve screens across three groups. Every one needs **loading / empty / error**
states designed, not just the happy path.

### Group A — Auth

**A1. Login** (`/login`)
Email + password only. No role picker — the account already knows its role, and
after sign-in the app routes providers to their dashboard and customers to
search. Link to register. Errors appear inline, not as alerts.

**A2. Register** (`/register`)
Email, password, and **the one role choice in the whole product**: "Book
services (customer)" vs "Offer services (provider)". This decision is permanent
and cannot be changed later, so it deserves visual weight — two large choice
cards, not a dropdown. Signup logs the user straight in.

**A3. Home / landing** (`/`)
Post-login stop showing email, a role badge, and one clear onward action ("Go to
your dashboard" / "Find a provider"). Currently plain — it could become a proper
welcome.

---

### Group B — Customer

**B1. Search** (`/search`) — *the most important screen in the app*
- **Where to look:** a map picker led by a place-search box ("Koramangala,
  Bengaluru"), a "Use my current location" action, and a draggable pin. Picking
  a city zooms out; picking a street zooms in.
- **Filters:** service category, mode (on-site / chat / any), radius in km.
- **Results:** ranked by rating, then distance. Each row shows name, truncated
  bio, **distance badge**, and rating with review count — or "No reviews yet",
  which must not look like a failure.
- **Empty state:** "No providers matched" with a nudge to widen the radius.

**B2. Provider detail** (`/providers/[id]`)
Name, rating badge (★ average + count), bio. Then **Services** — one card per
offering showing current price, booking type (instant vs consultation),
consultation fee if any, supported modes, and duration. Then **Reviews**.
Primary action: **Book**.
The critical distinction: an *instant* offering needs a date/time before
booking; a *consultation* offering does not, because the price isn't known yet.

**B3. My bookings** (`/bookings`)
A list of every booking with a status badge and enough context to tell two
similar jobs apart — service, provider, when. Empty state should point back to
search.

**B4. Booking detail** (`/bookings/[id]`) — *the densest screen*
Five stacked sections:
1. **Header card** — service name, provider, status badge, scheduled time,
   price or estimate.
2. **Actions** — depends on status: accept an estimate and pick a slot, or
   cancel.
3. **Payments** — advance (30%), final, or consultation fee. Amounts are
   server-calculated; the UI previews them. Each payment shows kind, amount,
   status.
4. **Messages** — live chat with the provider, once the booking is active.
5. **Review** — only after the job is completed. Star rating + comment.

This screen is a **state machine**: `PENDING_ESTIMATE → ESTIMATED → CONFIRMED →
COMPLETED`, plus `CANCELLED`. Design all five. Showing the customer where they
are in that sequence — a stepper or progress indicator — would be a real
improvement over today's single badge.

---

### Group C — Provider

**C1. Onboarding** (`/onboarding`)
Full name, short bio, **how far will you travel (km)**, and location via the
same map picker. This is a provider's first impression of the product and
should feel welcoming, not like a form. Manual latitude/longitude stays hidden
behind a small "Enter coordinates manually" link.

**C2. Dashboard** (`/dashboard`)
Two entirely different states:
- **Not onboarded** — a welcome card explaining what to do first.
- **Onboarded** — profile summary (name, rating, service radius), an
  **accepting-bookings toggle**, and the bookings panel.

The bookings panel is where a provider works: give an estimate on a
consultation request, mark a job complete, or cancel. Provider-side wording
differs from the customer's — `ESTIMATED` reads "Awaiting customer" here.

**C3. Offerings** (`/offerings`)
Full CRUD over what a provider sells. Each offering: category, base price,
booking type, consultation fee, supported modes, duration, and active/paused.
Category is **immutable after creation** — show it read-only when editing, and
make that legible rather than mysterious. A provider can't list the same
category twice.

**Worth designing:** the relationship between **base price** (what the provider
sets) and **current price** (what the rating-driven engine computes). Providers
need to understand why their price moved. Nothing in the UI explains this today
— it's the biggest gap.

---

## 5. Vocabulary (use these exact words)

| Concept | Values |
|---|---|
| Booking status | `PENDING_ESTIMATE`, `ESTIMATED`, `CONFIRMED`, `COMPLETED`, `CANCELLED` |
| Booking type | `INSTANT`, `CONSULTATION_REQUIRED` |
| Service mode | `ONSITE`, `CHAT` |
| Payment kind | `CONSULTATION`, `ADVANCE`, `FINAL` |
| Payment status | `PENDING`, `SUCCEEDED`, `FAILED` |
| Roles | `CUSTOMER`, `PROVIDER` |

Never show these raw strings to users — each needs human wording, and the
customer's wording differs from the provider's for the same status.

---

## 6. What to produce

In priority order:

1. **Design tokens + core components** (Button, Input, Field, Card, Badge) in
   light and dark. Everything else depends on these.
2. **B1 Search** and **B4 Booking detail** — the two screens that carry the
   product.
3. **C2 Dashboard** and **C3 Offerings** — the provider's daily surface.
4. Everything else.

Deliver each screen at **360px** and **1280px**, with loading, empty, and error
states shown alongside the happy path.
