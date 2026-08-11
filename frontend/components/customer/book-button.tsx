"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Field, Input, Select, Textarea } from "@/components/ui";
import { apiSend } from "@/lib/api-client";
import { firstError } from "@/lib/errors";
import type { PublicOffering } from "@/lib/types";

export default function BookButton({ offering }: { offering: PublicOffering }) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState(offering.supported_modes[0]);
  const [startAt, setStartAt] = useState("");
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const isInstant = offering.booking_type === "INSTANT";

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    const payload: Record<string, unknown> = { offering: offering.id, mode, notes };
    if (isInstant) {
      if (!startAt) {
        setError("Pick a time for your booking.");
        return;
      }
      // datetime-local is wall-clock with no zone; toISOString normalises it.
      payload.start_at = new Date(startAt).toISOString();
    }
    setSubmitting(true);
    const res = await apiSend("/bookings", "POST", payload);
    setSubmitting(false);
    if (res.ok) {
      const booking = await res.json();
      router.push(`/bookings/${booking.id}`);
      return;
    }
    const data = await res.json().catch(() => null);
    setError(firstError(data, "Couldn't create this booking."));
  }

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500"
      >
        {isInstant ? "Book now" : "Request consultation"}
      </button>
    );
  }

  return (
    <form onSubmit={submit} className="mt-3 space-y-3 rounded-lg border border-neutral-200 p-4 dark:border-neutral-800">
      <Field label="Mode">
        <Select value={mode} onChange={(e) => setMode(e.target.value as typeof mode)}>
          {offering.supported_modes.map((m) => (
            <option key={m} value={m}>
              {m === "CHAT" ? "Chat" : "On-site"}
            </option>
          ))}
        </Select>
      </Field>

      {isInstant && (
        <Field label="When">
          <Input
            type="datetime-local"
            value={startAt}
            onChange={(e) => setStartAt(e.target.value)}
          />
        </Field>
      )}

      <Field label="Notes (optional)">
        <Textarea
          rows={2}
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Describe what you need."
        />
      </Field>

      {!isInstant && Number(offering.consultation_fee) > 0 && (
        <p className="text-xs text-neutral-500">
          A consultation fee of ₹{offering.consultation_fee} applies, credited toward the final total.
        </p>
      )}

      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="flex gap-2">
        <button
          type="submit"
          disabled={submitting}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-60"
        >
          {submitting ? "Submitting…" : "Confirm"}
        </button>
        <button
          type="button"
          onClick={() => setOpen(false)}
          className="rounded-lg border border-neutral-300 px-4 py-2 text-sm font-medium text-neutral-700 hover:bg-neutral-100 dark:border-neutral-700 dark:text-neutral-200 dark:hover:bg-neutral-800"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}
