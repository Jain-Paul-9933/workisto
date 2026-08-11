import Link from "next/link";
import { notFound } from "next/navigation";

import BookButton from "@/components/customer/book-button";
import { Badge, Card } from "@/components/ui";
import { serverGet } from "@/lib/server-api";
import type { PublicProvider, Review } from "@/lib/types";

export default async function ProviderDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  const res = await serverGet(`/api/providers/${id}/`);
  if (res.status === 404) notFound();
  const provider: PublicProvider = await res.json();

  const reviewsRes = await serverGet(`/api/providers/${id}/reviews/`);
  const reviews: Review[] = reviewsRes.ok ? await reviewsRes.json() : [];

  return (
    <div className="space-y-8">
      <Link href="/search" className="text-sm text-indigo-600 hover:underline">
        ← Back to search
      </Link>

      <div>
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-semibold">{provider.full_name}</h1>
          {provider.rating_count > 0 && (
            <Badge tone="amber">★ {provider.rating_avg} ({provider.rating_count})</Badge>
          )}
        </div>
        {provider.bio && <p className="mt-2 max-w-2xl text-neutral-600 dark:text-neutral-300">{provider.bio}</p>}
      </div>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Services</h2>
        {provider.offerings.length === 0 ? (
          <p className="text-sm text-neutral-500">This provider has no active services right now.</p>
        ) : (
          <ul className="space-y-3">
            {provider.offerings.map((o) => (
              <li key={o.id}>
                <Card>
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="font-medium">{o.category_name}</p>
                      <p className="mt-1 text-sm text-neutral-500">
                        {o.booking_type === "INSTANT" ? "Instant booking" : "Consultation required"} ·{" "}
                        {o.supported_modes.map((m) => (m === "CHAT" ? "Chat" : "On-site")).join(", ")} ·{" "}
                        {o.duration_minutes} min
                      </p>
                    </div>
                    <p className="text-lg font-semibold">₹{o.current_price}</p>
                  </div>
                  <BookButton offering={o} />
                </Card>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Reviews</h2>
        {reviews.length === 0 ? (
          <p className="text-sm text-neutral-500">No reviews yet.</p>
        ) : (
          <ul className="space-y-3">
            {reviews.map((r) => (
              <li
                key={r.id}
                className="rounded-lg border border-neutral-200 p-4 dark:border-neutral-800"
              >
                <div className="flex items-center gap-2">
                  <span className="text-amber-500">{"★".repeat(r.rating)}</span>
                  <span className="text-sm font-medium">{r.reviewer}</span>
                </div>
                {r.comment && (
                  <p className="mt-1 text-sm text-neutral-600 dark:text-neutral-300">{r.comment}</p>
                )}
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
