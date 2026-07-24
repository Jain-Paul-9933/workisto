import Link from "next/link";
import { redirect } from "next/navigation";

import LogoutButton from "@/components/logout-button";
import { getCurrentUser } from "@/lib/session";

export default async function Home() {
  const user = await getCurrentUser();
  if (!user) redirect("/login");

  const isProvider = user.role === "PROVIDER";
  const homeHref = isProvider ? "/dashboard" : "/search";
  const homeLabel = isProvider ? "Go to your dashboard" : "Find a provider";

  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col justify-center gap-6 px-6">
      <div className="space-y-1">
        <p className="text-sm text-neutral-500">Signed in as</p>
        <p className="text-lg font-medium">{user.email}</p>
        <span className="inline-block rounded-full bg-indigo-100 px-2.5 py-0.5 text-xs font-medium text-indigo-700">
          {user.role}
        </span>
      </div>
      <div className="flex items-center gap-3">
        <Link
          href={homeHref}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-indigo-500"
        >
          {homeLabel}
        </Link>
        <LogoutButton />
      </div>
    </main>
  );
}
