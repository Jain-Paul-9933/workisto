import Link from "next/link";
import { notFound } from "next/navigation";

import BookingActions from "@/components/customer/booking-actions";
import ChatBox from "@/components/customer/chat-box";
import PaymentsPanel from "@/components/customer/payments-panel";
import ReviewForm from "@/components/customer/review-form";
import { Badge, Card } from "@/components/ui";
import { customerStatus, formatWhen } from "@/lib/booking-format";
import { serverGet } from "@/lib/server-api";
import type { Booking } from "@/lib/types";

export default async function BookingDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  const res = await serverGet(`/api/bookings/${id}/`);
  if (res.status === 404) notFound();
  const booking: Booking = await res.json();
  const st = customerStatus(booking.status);

  return (
    <div className="space-y-8">
      <Link href="/bookings" className="text-sm text-indigo-600 hover:underline">
        ← My bookings
      </Link>

      <Card>
        <div className="flex items-start justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold">{booking.category_name}</h1>
            <p className="mt-1 text-sm text-neutral-500">
              {booking.provider_name} · {booking.mode === "CHAT" ? "Chat" : "On-site"}
            </p>
          </div>
          <Badge tone={st.tone}>{st.label}</Badge>
        </div>

        <dl className="mt-4 grid grid-cols-2 gap-4 text-sm sm:grid-cols-3">
          <div>
            <dt className="text-neutral-500">When</dt>
            <dd className="font-medium">{formatWhen(booking.start_at)}</dd>
          </div>
          {booking.estimate_amount && (
            <div>
              <dt className="text-neutral-500">Estimate</dt>
              <dd className="font-medium">₹{booking.estimate_amount}</dd>
            </div>
          )}
          {booking.price && (
            <div>
              <dt className="text-neutral-500">Price</dt>
              <dd className="font-medium">₹{booking.price}</dd>
            </div>
          )}
          {Number(booking.consultation_fee) > 0 && (
            <div>
              <dt className="text-neutral-500">Consultation fee</dt>
              <dd className="font-medium">₹{booking.consultation_fee}</dd>
            </div>
          )}
        </dl>

        {booking.notes && (
          <p className="mt-4 text-sm italic text-neutral-500">&ldquo;{booking.notes}&rdquo;</p>
        )}
      </Card>

      <BookingActions booking={booking} />

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Payments</h2>
        <PaymentsPanel booking={booking} />
      </section>

      {booking.status !== "CANCELLED" && (
        <section className="space-y-3">
          <h2 className="text-lg font-semibold">Messages</h2>
          <ChatBox bookingId={booking.id} meId={booking.customer} />
        </section>
      )}

      {booking.status === "COMPLETED" && (
        <section className="space-y-3">
          <h2 className="text-lg font-semibold">Leave a review</h2>
          <ReviewForm booking={booking} />
        </section>
      )}
    </div>
  );
}
