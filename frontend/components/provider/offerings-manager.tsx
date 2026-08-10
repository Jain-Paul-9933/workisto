"use client";

import { useCallback, useState } from "react";

import { Badge, Button, Card, ErrorText, Field, Input, Select } from "@/components/ui";
import { apiGet, apiSend } from "@/lib/api-client";
import { firstError } from "@/lib/errors";
import type { BookingType, Category, Offering, ServiceMode } from "@/lib/types";

const MODES: { value: ServiceMode; label: string }[] = [
  { value: "ONSITE", label: "On-site" },
  { value: "CHAT", label: "Chat" },
];

// One form, two jobs: create a new offering, or edit an existing one. Category
// is the offering's identity — chosen once on create, shown read-only on edit
// (the backend rejects changing it).
function OfferingForm({
  offering,
  categories,
  takenCategoryIds,
  onSaved,
  onCancel,
}: {
  offering?: Offering;
  categories: Category[];
  takenCategoryIds: number[];
  onSaved: () => void;
  onCancel: () => void;
}) {
  const editing = !!offering;
  const available = categories.filter((c) => !takenCategoryIds.includes(c.id));

  const [category, setCategory] = useState<number | "">(
    offering?.category ?? available[0]?.id ?? "",
  );
  const [basePrice, setBasePrice] = useState(offering?.base_price ?? "");
  const [bookingType, setBookingType] = useState<BookingType>(offering?.booking_type ?? "INSTANT");
  const [consultationFee, setConsultationFee] = useState(offering?.consultation_fee ?? "0");
  const [modes, setModes] = useState<ServiceMode[]>(offering?.supported_modes ?? ["ONSITE"]);
  const [duration, setDuration] = useState(String(offering?.duration_minutes ?? 30));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  function toggleMode(m: ServiceMode) {
    setModes((cur) => (cur.includes(m) ? cur.filter((x) => x !== m) : [...cur, m]));
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (modes.length === 0) {
      setError("Pick at least one way customers can book — on-site or chat.");
      return;
    }
    if (!editing && category === "") {
      setError("Choose a service category.");
      return;
    }
    setSaving(true);
    const payload: Record<string, unknown> = {
      base_price: basePrice,
      booking_type: bookingType,
      consultation_fee: bookingType === "CONSULTATION_REQUIRED" ? consultationFee : "0",
      supported_modes: modes,
      duration_minutes: Number(duration),
    };
    if (!editing) payload.category = category;

    const res = editing
      ? await apiSend(`/providers/me/offerings/${offering!.id}`, "PATCH", payload)
      : await apiSend("/providers/me/offerings", "POST", payload);
    setSaving(false);
    if (res.ok) {
      onSaved();
      return;
    }
    const data = await res.json().catch(() => null);
    setError(firstError(data, "Couldn't save this offering."));
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      {editing ? (
        <div>
          <span className="text-sm font-medium text-neutral-700 dark:text-neutral-300">Service</span>
          <p className="mt-1 font-medium">{offering!.category_name}</p>
        </div>
      ) : (
        <Field label="Service category">
          <Select value={category} onChange={(e) => setCategory(Number(e.target.value))}>
            {available.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </Select>
        </Field>
      )}

      <div className="grid grid-cols-2 gap-3">
        <Field label="Base price (₹)">
          <Input
            type="number"
            min="0"
            step="0.01"
            required
            value={basePrice}
            onChange={(e) => setBasePrice(e.target.value)}
            placeholder="500.00"
          />
        </Field>
        <Field label="Duration (minutes)">
          <Input
            type="number"
            min="1"
            required
            value={duration}
            onChange={(e) => setDuration(e.target.value)}
          />
        </Field>
      </div>

      <Field label="Booking type">
        <Select value={bookingType} onChange={(e) => setBookingType(e.target.value as BookingType)}>
          <option value="INSTANT">Instant booking</option>
          <option value="CONSULTATION_REQUIRED">Consultation required</option>
        </Select>
      </Field>

      {bookingType === "CONSULTATION_REQUIRED" && (
        <Field label="Consultation fee (₹)">
          <Input
            type="number"
            min="0"
            step="0.01"
            value={consultationFee}
            onChange={(e) => setConsultationFee(e.target.value)}
            placeholder="0.00"
          />
        </Field>
      )}

      <div>
        <span className="text-sm font-medium text-neutral-700 dark:text-neutral-300">
          How can customers book this?
        </span>
        <div className="mt-2 flex gap-4">
          {MODES.map((m) => (
            <label key={m.value} className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={modes.includes(m.value)}
                onChange={() => toggleMode(m.value)}
                className="h-4 w-4 rounded border-neutral-300 text-indigo-600 focus:ring-indigo-500"
              />
              {m.label}
            </label>
          ))}
        </div>
      </div>

      <ErrorText>{error}</ErrorText>

      <div className="flex gap-2">
        <Button type="submit" disabled={saving} className="w-auto px-5">
          {saving ? "Saving…" : editing ? "Save changes" : "Add offering"}
        </Button>
        <button
          type="button"
          onClick={onCancel}
          className="rounded-lg border border-neutral-300 px-5 py-2.5 text-sm font-medium text-neutral-700 hover:bg-neutral-100 dark:border-neutral-700 dark:text-neutral-200 dark:hover:bg-neutral-800"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}

function OfferingCard({
  offering,
  categories,
  takenCategoryIds,
  onChanged,
}: {
  offering: Offering;
  categories: Category[];
  takenCategoryIds: number[];
  onChanged: () => void;
}) {
  const [editing, setEditing] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function mutate(method: "PATCH" | "DELETE", body?: unknown, fallback?: string) {
    setBusy(true);
    setError("");
    const res = await apiSend(`/providers/me/offerings/${offering.id}`, method, body);
    setBusy(false);
    if (res.ok) {
      onChanged();
      return;
    }
    const data = await res.json().catch(() => null);
    setError(firstError(data, fallback));
  }

  if (editing) {
    return (
      <li>
        <Card>
          <OfferingForm
            offering={offering}
            categories={categories}
            takenCategoryIds={takenCategoryIds}
            onSaved={() => {
              setEditing(false);
              onChanged();
            }}
            onCancel={() => setEditing(false)}
          />
        </Card>
      </li>
    );
  }

  const priceMoved = offering.current_price !== offering.base_price;

  return (
    <li className="rounded-xl border border-neutral-200 bg-white p-5 dark:border-neutral-800 dark:bg-neutral-900">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <p className="font-medium">{offering.category_name}</p>
            <Badge tone={offering.is_active ? "green" : "neutral"}>
              {offering.is_active ? "Active" : "Paused"}
            </Badge>
          </div>
          <p className="mt-1 text-sm text-neutral-500">
            {offering.booking_type === "INSTANT" ? "Instant booking" : "Consultation required"} ·{" "}
            {offering.supported_modes
              .map((m) => (m === "CHAT" ? "Chat" : "On-site"))
              .join(", ")}{" "}
            · {offering.duration_minutes} min
          </p>
        </div>
        <div className="text-right">
          <p className="font-semibold">₹{offering.current_price}</p>
          {priceMoved && (
            <p className="text-xs text-neutral-400 line-through">₹{offering.base_price}</p>
          )}
        </div>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={() => setEditing(true)}
          disabled={busy}
          className="rounded-lg border border-neutral-300 px-3 py-1.5 text-sm font-medium text-neutral-700 hover:bg-neutral-100 disabled:opacity-60 dark:border-neutral-700 dark:text-neutral-200 dark:hover:bg-neutral-800"
        >
          Edit
        </button>
        <button
          type="button"
          onClick={() => mutate("PATCH", { is_active: !offering.is_active }, "Couldn't update this offering.")}
          disabled={busy}
          className="rounded-lg border border-neutral-300 px-3 py-1.5 text-sm font-medium text-neutral-700 hover:bg-neutral-100 disabled:opacity-60 dark:border-neutral-700 dark:text-neutral-200 dark:hover:bg-neutral-800"
        >
          {offering.is_active ? "Pause" : "Activate"}
        </button>
        <button
          type="button"
          onClick={() => mutate("DELETE", undefined, "Couldn't delete this offering.")}
          disabled={busy}
          className="rounded-lg px-3 py-1.5 text-sm font-medium text-red-600 hover:bg-red-50 disabled:opacity-60 dark:hover:bg-red-950/40"
        >
          Delete
        </button>
      </div>

      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
    </li>
  );
}

export default function OfferingsManager({
  initialOfferings,
  categories,
}: {
  initialOfferings: Offering[];
  categories: Category[];
}) {
  const [offerings, setOfferings] = useState(initialOfferings);
  const [creating, setCreating] = useState(false);

  const reload = useCallback(async () => {
    const res = await apiGet("/providers/me/offerings");
    if (res.ok) setOfferings(await res.json());
  }, []);

  const takenCategoryIds = offerings.map((o) => o.category);
  const available = categories.filter((c) => !takenCategoryIds.includes(c.id));

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Your offerings</h1>
          <p className="mt-1 text-sm text-neutral-500">
            Each service you offer, its price, and how customers can book it.
          </p>
        </div>
        {!creating && available.length > 0 && (
          <button
            type="button"
            onClick={() => setCreating(true)}
            className="shrink-0 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500"
          >
            New offering
          </button>
        )}
      </div>

      {creating && (
        <Card>
          <h2 className="mb-4 font-medium">New offering</h2>
          <OfferingForm
            categories={categories}
            takenCategoryIds={takenCategoryIds}
            onSaved={() => {
              setCreating(false);
              reload();
            }}
            onCancel={() => setCreating(false)}
          />
        </Card>
      )}

      {offerings.length === 0 && !creating && (
        <Card>
          <p className="text-sm text-neutral-500">
            You haven&rsquo;t added any services yet. Add your first offering so customers can book you.
          </p>
        </Card>
      )}

      <ul className="space-y-3">
        {offerings.map((o) => (
          <OfferingCard
            key={o.id}
            offering={o}
            categories={categories}
            takenCategoryIds={takenCategoryIds}
            onChanged={reload}
          />
        ))}
      </ul>

      {available.length === 0 && categories.length > 0 && (
        <p className="text-xs text-neutral-500">
          You&rsquo;re offering every available category. New categories are added via the admin.
        </p>
      )}
    </div>
  );
}
