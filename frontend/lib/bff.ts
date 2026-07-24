import { cookies } from "next/headers";

import { BACKEND_URL } from "./config";

const UNSAFE = new Set(["POST", "PUT", "PATCH", "DELETE"]);

/**
 * The BFF core: forward a browser request to Django, keeping the browser out of
 * the token business (ADR 0001).
 *
 * - The httpOnly session cookie rides along in the `Cookie` header.
 * - For unsafe methods we lift the `csrftoken` cookie into the `X-CSRFToken`
 *   header, which is what DRF's SessionAuthentication checks.
 * - Django's `Set-Cookie` (session, csrf) is relayed back so the browser stores
 *   it against the Next origin.
 */
export async function proxy(req: Request, backendPath: string): Promise<Response> {
  const jar = await cookies();
  const cookieHeader = jar.toString();

  const headers: Record<string, string> = {};
  const contentType = req.headers.get("content-type");
  if (contentType) headers["Content-Type"] = contentType;
  if (cookieHeader) headers["Cookie"] = cookieHeader;

  let body: string | undefined;
  if (UNSAFE.has(req.method)) {
    const csrf = jar.get("csrftoken")?.value;
    if (csrf) headers["X-CSRFToken"] = csrf;
    body = await req.text();
  }

  const upstream = await fetch(`${BACKEND_URL}${backendPath}`, {
    method: req.method,
    headers,
    body,
    redirect: "manual",
    cache: "no-store",
  });

  const out = new Response(upstream.body, {
    status: upstream.status,
    statusText: upstream.statusText,
  });
  const ct = upstream.headers.get("content-type");
  if (ct) out.headers.set("Content-Type", ct);
  for (const cookie of upstream.headers.getSetCookie()) {
    out.headers.append("Set-Cookie", cookie);
  }
  return out;
}
