import Link from "next/link";
import { redirect } from "next/navigation";

import LogoutButton from "@/components/logout-button";
import { getCurrentUser } from "@/lib/session";

// Shared chrome for the customer journey. Providers are bounced to their own
// side; the proxy already gates this, so this is defense in depth + the header.
export default async function CustomerLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const user = await getCurrentUser();
  if (!user) redirect("/login");
  if (user.role === "PROVIDER") redirect("/dashboard");

  return (
    <div className="min-h-screen bg-neutral-50 dark:bg-neutral-950">
      <header className="border-b border-neutral-200 bg-white dark:border-neutral-800 dark:bg-neutral-900">
        <div className="mx-auto flex max-w-4xl items-center justify-between px-6 py-3">
          <div className="flex items-center gap-6">
            <Link href="/search" className="text-lg font-semibold text-indigo-600">
              Workisto
            </Link>
            <nav className="flex items-center gap-4 text-sm">
              <Link
                href="/search"
                className="text-neutral-600 hover:text-neutral-900 dark:text-neutral-300 dark:hover:text-white"
              >
                Find a provider
              </Link>
              <Link
                href="/bookings"
                className="text-neutral-600 hover:text-neutral-900 dark:text-neutral-300 dark:hover:text-white"
              >
                My bookings
              </Link>
            </nav>
          </div>
          <LogoutButton />
        </div>
      </header>
      <main className="mx-auto max-w-4xl px-6 py-8">{children}</main>
    </div>
  );
}
