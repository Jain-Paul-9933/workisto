"use client";

import { useCallback, useEffect, useState } from "react";

import { Badge } from "@/components/ui";
import { apiGet, apiSend } from "@/lib/api-client";
import { firstError } from "@/lib/errors";
import type { Booking, Payment, PaymentKind, PaymentStatus } from "@/lib/types";

const STATUS_TONE: Record<PaymentStatus, "neutral" | "green" | "amber" | "red"> = {
  PENDING: "amber",
  SUCCEEDED: "green",
  FAILED: "red",
  REFUNDED: "neutral",
};

const ADVANCE_FRACTION = 0.3;

function round2(n: number): string {
  return (Math.round(n * 100) / 100).toFixed(2);
}

const KIND_LABEL: Record<PaymentKind, string> = {
  CONSULTATION: "Consultation fee",
  ADVANCE: "Advance (30%)",
  FINAL: "Final balance",
};

export default function PaymentsPanel({ booking }: { booking: Booking }) {
  const [payments, setPayments] = useState<Payment[] | null>(null);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    const res = await apiGet(`/bookings/${booking.id}/payments`);
    if (res.ok) setPayments(await res.json());
    else setError("Couldn't load payments.");
  }, [booking.id]);

  useEffect(() => {
    load();
  }, [load]);

  async function pay(kind: PaymentKind) {
    setBusy(kind);
    setError("");
    const res = await apiSend(`/bookings/${booking.id}/pay`, "POST", { kind });
    setBusy("");
    if (res.ok) {
      load();
      return;
    }
    const data = await res.json().catch(() => null);
    setError(firstError(data, "Couldn't start that payment."));
  }

  if (payments === null) return <p className="text-sm text-neutral-500">Loading payments…</p>;

  const succeeded = new Set(
    payments.filter((p) => p.status === "SUCCEEDED").map((p) => p.kind),
  );
  const consultationPaid = succeeded.has("CONSULTATION");

  // Server computes the authoritative amount; these previews mirror its formula.
  const price = Number(booking.price ?? 0);
  const fee = Number(booking.consultation_fee ?? 0);
  const advance = price * ADVANCE_FRACTION;
  const finalDue = Math.max(0, price - advance - (consultationPaid ? fee : 0));

  const payable: { kind: PaymentKind; amount: string }[] = [];
  const active = booking.status !== "CANCELLED";
  if (active && fee > 0 && !succeeded.has("CONSULTATION")) {
    payable.push({ kind: "CONSULTATION", amount: round2(fee) });
  }
  // Advance/final need a price, which is only set once the booking is confirmed.
  if (active && price > 0 && !succeeded.has("ADVANCE")) {
    payable.push({ kind: "ADVANCE", amount: round2(advance) });
  }
  if (active && price > 0 && !succeeded.has("FINAL")) {
    payable.push({ kind: "FINAL", amount: round2(finalDue) });
  }

  return (
    <div className="space-y-4">
      {payments.length > 0 && (
        <ul className="space-y-2">
          {payments.map((p) => (
            <li
              key={p.id}
              className="flex items-center justify-between rounded-lg border border-neutral-200 px-4 py-2 text-sm dark:border-neutral-800"
            >
              <span>
                {KIND_LABEL[p.kind]} · ₹{p.amount}
              </span>
              <Badge tone={STATUS_TONE[p.status]}>{p.status.toLowerCase()}</Badge>
            </li>
          ))}
        </ul>
      )}

      {payable.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {payable.map((item) => (
            <button
              key={item.kind}
              type="button"
              onClick={() => pay(item.kind)}
              disabled={busy !== ""}
              className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-60"
            >
              {busy === item.kind ? "Starting…" : `Pay ${KIND_LABEL[item.kind].toLowerCase()} · ₹${item.amount}`}
            </button>
          ))}
        </div>
      )}

      {payments.length === 0 && payable.length === 0 && (
        <p className="text-sm text-neutral-500">Nothing to pay yet.</p>
      )}

      {error && <p className="text-sm text-red-600">{error}</p>}

      <p className="text-xs text-neutral-400">
        Payments settle when the gateway confirms via a signed webhook — the server, not the
        client, marks them succeeded.
      </p>
    </div>
  );
}
