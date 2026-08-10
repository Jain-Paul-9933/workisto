"use client";

import { useState } from "react";

import { apiSend } from "@/lib/api-client";
import { firstError } from "@/lib/errors";

// The provider's on/off switch for taking new work. Search excludes providers
// who aren't accepting, so this is their "I'm booked up" lever.
export default function AcceptingToggle({ initial }: { initial: boolean }) {
  const [on, setOn] = useState(initial);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function toggle() {
    const next = !on;
    setSaving(true);
    setError("");
    const res = await apiSend("/providers/me", "PATCH", { accepting_bookings: next });
    setSaving(false);
    if (res.ok) {
      setOn(next);
      return;
    }
    const data = await res.json().catch(() => null);
    setError(firstError(data, "Couldn't update your availability."));
  }

  return (
    <div className="flex items-center gap-3">
      <button
        type="button"
        role="switch"
        aria-checked={on}
        onClick={toggle}
        disabled={saving}
        className={
          "relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition disabled:opacity-60 " +
          (on ? "bg-green-500" : "bg-neutral-300 dark:bg-neutral-700")
        }
      >
        <span
          className={
            "inline-block h-5 w-5 transform rounded-full bg-white shadow transition " +
            (on ? "translate-x-5" : "translate-x-0.5")
          }
        />
      </button>
      <span className="text-sm text-neutral-600 dark:text-neutral-300">
        {on ? "Accepting bookings" : "Not accepting bookings"}
      </span>
      {error && <span className="text-sm text-red-600">{error}</span>}
    </div>
  );
}
