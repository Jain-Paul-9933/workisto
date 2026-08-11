import type { BookingStatus } from "./types";

type Tone = "neutral" | "green" | "amber" | "red" | "indigo";

// Customer-side status wording (a provider sees different labels for the same
// states — see components/provider/bookings-panel).
const CUSTOMER: Record<BookingStatus, { label: string; tone: Tone }> = {
  PENDING_ESTIMATE: { label: "Awaiting estimate", tone: "amber" },
  ESTIMATED: { label: "Estimate ready", tone: "indigo" },
  CONFIRMED: { label: "Confirmed", tone: "green" },
  COMPLETED: { label: "Completed", tone: "neutral" },
  CANCELLED: { label: "Cancelled", tone: "red" },
};

export function customerStatus(status: BookingStatus) {
  return CUSTOMER[status];
}

export function formatWhen(iso: string | null): string {
  if (!iso) return "Not scheduled";
  return new Date(iso).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}
