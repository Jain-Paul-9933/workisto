import { redirect } from "next/navigation";

import LogoutButton from "@/components/logout-button";
import { getCurrentUser } from "@/lib/session";

export default async function CustomerSearch() {
  const user = await getCurrentUser();
  if (!user) redirect("/login");

  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col justify-center gap-4 px-6">
      <h1 className="text-2xl font-semibold">Find a provider</h1>
      <p className="text-neutral-500">
        Signed in as {user.email}. Geo search, provider profiles, booking, and
        chat land here as the customer flow is built.
      </p>
      <div>
        <LogoutButton />
      </div>
    </main>
  );
}
