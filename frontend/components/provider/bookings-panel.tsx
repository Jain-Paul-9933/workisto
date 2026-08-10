"use client";

import { useCallback, useEffect, useState } from "react";

import { Badge } from "@/components/ui";
import { apiGet, apiSend } from "@/lib/api-client";
import { firstError } from "@/lib/errors";
import type { Booking, BookingStatus } from "@/lib/types";

const STATUS_TONE: Record<BookingStatus, "neutral" | "green" | "amber" | "red" | "indigo"> = {
  PENDING_ESTIMATE: "amber",
  ESTIMATED: "indigo",
  CONFIRMED: "green",
  COMPLETED: "neutral",
  CANCELLED: "red",
};

// Provider-side labels — from the provider's point of view an ESTIMATED booking
// is "waiting on the customer to confirm".
const STATUS_LABEL: Record<BookingStatus, string> = {
  PENDING_ESTIMATE: "Needs estimate",
  ESTIMATED: "Awaiting customer",
  CONFIRMED: "Confirmed",
  COMPLETED: "Completed",
  CANCELLED: "Cancelled",
};

function formatWhen(iso: string | null): string {
  if (!iso) return "Not scheduled";
  return new Date(iso).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

type ActionButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  kind?: "primary" | "ghost";
};

function ActionButton({ kind = "primary", type = "button", ...props }: ActionButtonProps) {
  const styles =
    kind === "primary"
      ? "bg-indigo-600 text-white hover:bg-indigo-500"
      : "border border-neutral-300 text-neutral-700 hover:bg-neutral-100 dark:border-neutral-700 dark:text-neutral-200 dark:hover:bg-neutral-800";
  return (
    <button
      type={type}
      className={"rounded-lg px-3 py-1.5 text-sm font-medium transition disabled:opacity-60 " + styles}
      {...props}
    />
  );
}

function BookingRow({ booking, onChanged }: { booking: Booking; onChanged: () => void }) {
  const [estimate, setEstimate] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function act(path: string, body?: unknown) {
    setBusy(true);
    setError("");
    const res = await apiSend(path, "POST", body);
    setBusy(false);
    if (res.ok) {
      onChanged();
      return;
    }
    const data = await res.json().catch(() => null);
    setError(firstError(data, "That didn't go through. Please try again."));
  }

  const canCancel = booking.status !== "COMPLETED" && booking.status !== "CANCELLED";

  return (
    <li className="rounded-lg border border-neutral-200 p-4 dark:border-neutral-800">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="font-medium">{booking.category_name}</p>
          <p className="text-sm text-neutral-500">
            {booking.mode === "CHAT" ? "Chat" : "On-site"} · {formatWhen(booking.start_at)}
          </p>
        </div>
        <Badge tone={STATUS_TONE[booking.status]}>{STATUS_LABEL[booking.status]}</Badge>
      </div>

      <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-sm text-neutral-600 dark:text-neutral-300">
        {booking.estimate_amount && <span>Estimate ₹{booking.estimate_amount}</span>}
        {booking.price && <span>Price ₹{booking.price}</span>}
        {Number(booking.consultation_fee) > 0 && <span>Consultation ₹{booking.consultation_fee}</span>}
      </div>

      {booking.notes && (
        <p className="mt-2 text-sm italic text-neutral-500">&ldquo;{booking.notes}&rdquo;</p>
      )}

      <div className="mt-3 flex flex-wrap items-center gap-2">
        {booking.status === "PENDING_ESTIMATE" && (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (estimate) act(`/bookings/${booking.id}/estimate`, { estimate_amount: estimate });
            }}
            className="flex items-center gap-2"
          >
            <input
              type="number"
              min="0"
              step="0.01"
              required
              placeholder="Amount"
              value={estimate}
              onChange={(e) => setEstimate(e.target.value)}
              className="w-28 rounded-lg border border-neutral-300 bg-white px-3 py-1.5 text-sm outline-none focus:border-indigo-500 dark:border-neutral-700 dark:bg-neutral-900"
            />
            <ActionButton type="submit" disabled={busy}>
              Send estimate
            </ActionButton>
          </form>
        )}
        {booking.status === "CONFIRMED" && (
          <ActionButton disabled={busy} onClick={() => act(`/bookings/${booking.id}/complete`)}>
            Mark complete
          </ActionButton>
        )}
        {canCancel && (
          <ActionButton kind="ghost" disabled={busy} onClick={() => act(`/bookings/${booking.id}/cancel`)}>
            Cancel
          </ActionButton>
        )}
      </div>

      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
    </li>
  );
}

export default function BookingsPanel() {
  const [bookings, setBookings] = useState<Booking[] | null>(null);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    const res = await apiGet("/bookings");
    if (!res.ok) {
      setError("Couldn't load your bookings.");
      return;
    }
    setError("");
    setBookings(await res.json());
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  if (error) return <p className="text-sm text-red-600">{error}</p>;
  if (bookings === null) return <p className="text-sm text-neutral-500">Loading bookings…</p>;
  if (bookings.length === 0) {
    return (
      <p className="text-sm text-neutral-500">
        No bookings yet. They&rsquo;ll show up here as customers request your services.
      </p>
    );
  }

  return (
    <ul className="space-y-3">
      {bookings.map((b) => (
        <BookingRow key={b.id} booking={b} onChanged={load} />
      ))}
    </ul>
  );
}
