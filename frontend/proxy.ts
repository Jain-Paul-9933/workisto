import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// Next.js 16 renamed `middleware` → `proxy` (same behaviour). This gates routes
// by auth + role. It's UX-level routing; the backend is the real authority
// (every API view is permission-checked server-side).

const PUBLIC_PATHS = ["/login", "/register"];
const PROVIDER_PREFIXES = ["/dashboard", "/onboarding", "/offerings"];
const CUSTOMER_PREFIXES = ["/search", "/providers", "/bookings"];

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const loggedIn = request.cookies.has("sessionid");
  const role = request.cookies.get("role")?.value;

  const isPublic = PUBLIC_PATHS.some((p) => pathname.startsWith(p));

  // Unauthenticated → only auth pages are reachable.
  if (!loggedIn) {
    if (isPublic) return NextResponse.next();
    return NextResponse.redirect(new URL("/login", request.url));
  }

  // Logged in but sitting on an auth page → send them home.
  if (isPublic) {
    const home = role === "PROVIDER" ? "/dashboard" : "/search";
    return NextResponse.redirect(new URL(home, request.url));
  }

  // Keep each role inside its own section.
  const wantsProvider = PROVIDER_PREFIXES.some((p) => pathname.startsWith(p));
  const wantsCustomer = CUSTOMER_PREFIXES.some((p) => pathname.startsWith(p));
  if (wantsProvider && role !== "PROVIDER") {
    return NextResponse.redirect(new URL("/search", request.url));
  }
  if (wantsCustomer && role === "PROVIDER") {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  return NextResponse.next();
}

export const config = {
  // Run on everything except Next internals, the BFF proxy, and static assets.
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};
