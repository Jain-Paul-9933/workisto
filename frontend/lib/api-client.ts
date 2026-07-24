"use client";

// Client-side calls always go through our own BFF (/api/bff/*), never straight
// to Django — so the browser only ever deals with the same origin.

async function ensureCsrf() {
  // Makes Django set the csrftoken cookie (relayed to us) before an unsafe call.
  // No trailing slash on the BFF path — Next strips it (308); the proxy re-adds
  // it for Django.
  await fetch("/api/bff/auth/csrf", { credentials: "same-origin" });
}

export async function apiGet(path: string) {
  return fetch(`/api/bff${path}`, { credentials: "same-origin" });
}

export async function apiSend(
  path: string,
  method: "POST" | "PUT" | "PATCH" | "DELETE",
  body?: unknown,
) {
  await ensureCsrf();
  return fetch(`/api/bff${path}`, {
    method,
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}

/** UX-only cookie so middleware can route by role. Real authz is the backend's. */
export function setRoleCookie(role: string) {
  document.cookie = `role=${role}; path=/; samesite=lax`;
}

export function clearRoleCookie() {
  document.cookie = "role=; path=/; max-age=0; samesite=lax";
}
