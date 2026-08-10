import Link from "next/link";

import AcceptingToggle from "@/components/provider/accepting-toggle";
import BookingsPanel from "@/components/provider/bookings-panel";
import { Card } from "@/components/ui";
import { serverGet } from "@/lib/server-api";
import type { Provider } from "@/lib/types";

export default async function ProviderDashboard() {
  const res = await serverGet("/api/providers/me/");

  // 404 = signed in as a provider, but hasn't onboarded yet.
  if (res.status === 404) {
    return (
      <Card>
        <h1 className="text-xl font-semibold">Welcome to Workisto</h1>
        <p className="mt-2 text-sm text-neutral-500">
          Let&rsquo;s set up your provider profile so customers nearby can find and book you.
        </p>
        <Link
          href="/onboarding"
          className="mt-4 inline-block rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500"
        >
          Set up your profile
        </Link>
      </Card>
    );
  }

  const provider: Provider = await res.json();

  return (
    <div className="space-y-8">
      <Card>
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold">{provider.full_name}</h1>
            {provider.bio && (
              <p className="mt-1 max-w-lg text-sm text-neutral-500">{provider.bio}</p>
            )}
          </div>
          <Link href="/onboarding" className="text-sm font-medium text-indigo-600 hover:underline">
            Edit profile
          </Link>
        </div>

        <dl className="mt-4 grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
          <div>
            <dt className="text-neutral-500">Rating</dt>
            <dd className="font-medium">
              {provider.rating_count > 0
                ? `★ ${provider.rating_avg} (${provider.rating_count})`
                : "No reviews yet"}
            </dd>
          </div>
          <div>
            <dt className="text-neutral-500">Travel radius</dt>
            <dd className="font-medium">{provider.service_radius_km} km</dd>
          </div>
          <div>
            <dt className="text-neutral-500">Location</dt>
            <dd className="font-medium">
              {provider.location
                ? `${provider.location.latitude.toFixed(4)}, ${provider.location.longitude.toFixed(4)}`
                : "Not set"}
            </dd>
          </div>
          <div>
            <dt className="text-neutral-500">Offerings</dt>
            <dd className="font-medium">
              <Link href="/offerings" className="text-indigo-600 hover:underline">
                Manage
              </Link>
            </dd>
          </div>
        </dl>

        <div className="mt-5 border-t border-neutral-200 pt-4 dark:border-neutral-800">
          <AcceptingToggle initial={provider.accepting_bookings} />
        </div>
      </Card>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Bookings</h2>
        <BookingsPanel />
      </section>
    </div>
  );
}
