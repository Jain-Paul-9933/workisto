import Link from "next/link";

import { Badge } from "@/components/ui";
import { customerStatus, formatWhen } from "@/lib/booking-format";
import { serverGet } from "@/lib/server-api";
import type { Booking } from "@/lib/types";

export default async function BookingsListPage() {
  const res = await serverGet("/api/bookings/");
  const bookings: Booking[] = res.ok ? await res.json() : [];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">My bookings</h1>

      {bookings.length === 0 ? (
        <p className="text-sm text-neutral-500">
          You haven&rsquo;t booked anything yet.{" "}
          <Link href="/search" className="text-indigo-600 hover:underline">
            Find a provider
          </Link>
          .
        </p>
      ) : (
        <ul className="space-y-3">
          {bookings.map((b) => {
            const st = customerStatus(b.status);
            return (
              <li key={b.id}>
                <Link
                  href={`/bookings/${b.id}`}
                  className="block rounded-xl border border-neutral-200 bg-white p-5 transition hover:border-indigo-300 hover:shadow-sm dark:border-neutral-800 dark:bg-neutral-900 dark:hover:border-indigo-700"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-medium">{b.category_name}</p>
                      <p className="mt-1 text-sm text-neutral-500">
                        {b.provider_name} · {b.mode === "CHAT" ? "Chat" : "On-site"} ·{" "}
                        {formatWhen(b.start_at)}
                      </p>
                    </div>
                    <Badge tone={st.tone}>{st.label}</Badge>
                  </div>
                </Link>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
