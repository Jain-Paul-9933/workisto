"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Field, Input } from "@/components/ui";
import { apiSend } from "@/lib/api-client";
import { firstError } from "@/lib/errors";
import type { Booking } from "@/lib/types";

// The customer's own controls on a booking: accept an estimate (picking a slot)
// or call the whole thing off. Provider-side actions live elsewhere.
export default function BookingActions({ booking }: { booking: Booking }) {
  const router = useRouter();
  const [startAt, setStartAt] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function post(path: string, body?: unknown) {
    setBusy(true);
    setError("");
    const res = await apiSend(path, "POST", body);
    setBusy(false);
    if (res.ok) {
      router.refresh();
      return;
    }
    const data = await res.json().catch(() => null);
    setError(firstError(data, "That didn't go through. Please try again."));
  }

  const canCancel = booking.status !== "COMPLETED" && booking.status !== "CANCELLED";

  return (
    <div className="space-y-3">
      {booking.status === "PENDING_ESTIMATE" && (
        <p className="text-sm text-neutral-500">
          Waiting for {booking.provider_name} to send an estimate.
        </p>
      )}

      {booking.status === "ESTIMATED" && (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (!startAt) {
              setError("Pick a time to confirm your booking.");
              return;
            }
            post(`/bookings/${booking.id}/confirm`, {
              start_at: new Date(startAt).toISOString(),
            });
          }}
          className="space-y-3 rounded-lg border border-indigo-200 bg-indigo-50 p-4 dark:border-indigo-900 dark:bg-indigo-950/30"
        >
          <p className="text-sm">
            Estimate: <span className="font-semibold">₹{booking.estimate_amount}</span>. Pick a
            time to confirm.
          </p>
          <Field label="When">
            <Input type="datetime-local" value={startAt} onChange={(e) => setStartAt(e.target.value)} />
          </Field>
          <button
            type="submit"
            disabled={busy}
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-60"
          >
            {busy ? "Confirming…" : "Accept & confirm"}
          </button>
        </form>
      )}

      {error && <p className="text-sm text-red-600">{error}</p>}

      {canCancel && (
        <button
          type="button"
          onClick={() => post(`/bookings/${booking.id}/cancel`)}
          disabled={busy}
          className="rounded-lg border border-neutral-300 px-4 py-2 text-sm font-medium text-neutral-700 hover:bg-neutral-100 disabled:opacity-60 dark:border-neutral-700 dark:text-neutral-200 dark:hover:bg-neutral-800"
        >
          Cancel booking
        </button>
      )}
    </div>
  );
}
