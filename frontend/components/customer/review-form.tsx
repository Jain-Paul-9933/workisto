"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Field, Select, Textarea } from "@/components/ui";
import { apiSend } from "@/lib/api-client";
import { firstError } from "@/lib/errors";
import type { Booking } from "@/lib/types";

// Only shown on a COMPLETED booking. One review per booking — if the customer
// already left one, the backend rejects it and we surface that message.
export default function ReviewForm({ booking }: { booking: Booking }) {
  const router = useRouter();
  const [rating, setRating] = useState("5");
  const [comment, setComment] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    const res = await apiSend("/reviews", "POST", {
      booking: booking.id,
      rating: Number(rating),
      comment,
    });
    setSubmitting(false);
    if (res.ok) {
      setDone(true);
      router.refresh();
      return;
    }
    const data = await res.json().catch(() => null);
    setError(firstError(data, "Couldn't submit your review."));
  }

  if (done) {
    return <p className="text-sm text-green-600">Thanks for your review!</p>;
  }

  return (
    <form onSubmit={submit} className="space-y-3">
      <Field label="Rating">
        <Select value={rating} onChange={(e) => setRating(e.target.value)}>
          {[5, 4, 3, 2, 1].map((n) => (
            <option key={n} value={n}>
              {"★".repeat(n)} ({n})
            </option>
          ))}
        </Select>
      </Field>
      <Field label="Comment (optional)">
        <Textarea
          rows={3}
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          placeholder="How did it go?"
        />
      </Field>
      {error && <p className="text-sm text-red-600">{error}</p>}
      <button
        type="submit"
        disabled={submitting}
        className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-60"
      >
        {submitting ? "Submitting…" : "Submit review"}
      </button>
    </form>
  );
}
