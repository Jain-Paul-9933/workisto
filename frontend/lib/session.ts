import { cookies } from "next/headers";

import { BACKEND_URL } from "./config";

export type User = {
  id: number;
  email: string;
  role: "CUSTOMER" | "PROVIDER" | "ADMIN";
  first_name: string;
  last_name: string;
};

/** Server-side "who am I": asks Django with the caller's cookies. */
export async function getCurrentUser(): Promise<User | null> {
  const cookieHeader = (await cookies()).toString();
  const res = await fetch(`${BACKEND_URL}/api/me/`, {
    headers: cookieHeader ? { Cookie: cookieHeader } : {},
    cache: "no-store",
  });
  if (!res.ok) return null;
  return res.json();
}
