"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { apiSend, clearRoleCookie } from "@/lib/api-client";

export default function LogoutButton() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  async function onClick() {
    setLoading(true);
    await apiSend("/auth/logout", "POST");
    clearRoleCookie();
    router.replace("/login");
    router.refresh();
  }

  return (
    <button
      onClick={onClick}
      disabled={loading}
      className="rounded-lg border border-neutral-300 px-4 py-2 text-sm font-medium text-neutral-700 transition hover:bg-neutral-100 disabled:opacity-60 dark:border-neutral-700 dark:text-neutral-200 dark:hover:bg-neutral-800"
    >
      {loading ? "Signing out…" : "Sign out"}
    </button>
  );
}
