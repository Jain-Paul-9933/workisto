import { cookies } from "next/headers";

import { BACKEND_URL } from "./config";

// Server-side GET straight to Django, forwarding the caller's cookies (session +
// CSRF). Returns the raw Response so callers can branch on status — e.g. a 404
// on /providers/me/ means "signed in, but not onboarded yet", not an error.
export async function serverGet(path: string): Promise<Response> {
  const cookieHeader = (await cookies()).toString();
  return fetch(`${BACKEND_URL}${path}`, {
    headers: cookieHeader ? { Cookie: cookieHeader } : {},
    cache: "no-store",
  });
}
