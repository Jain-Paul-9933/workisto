import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { BACKEND_URL, SEARCH_URL } from "@/lib/config";

// Search doesn't go through the generic BFF proxy because it fans out to two
// services: Django mints a short-lived token, then the async FastAPI read
// service answers the query with it (ADR 0001). The token is minted and used
// entirely server-side — the browser only ever sees results. If the search
// service is unreachable, we fall back to Django's own search endpoint.

type SearchRow = {
  id: number;
  full_name: string;
  bio: string;
  rating_avg: number;
  rating_count: number;
  distance_km: number;
};

// Django's search serializer renders rating_avg as a Decimal string; normalise
// it to a number so the client sees one shape regardless of source.
type DjangoRow = Omit<SearchRow, "rating_avg"> & { rating_avg: string };

export async function GET(req: Request) {
  const incoming = new URL(req.url).searchParams;
  const lat = incoming.get("lat");
  const lng = incoming.get("lng");
  if (!lat || !lng) {
    return NextResponse.json({ detail: "lat and lng are required." }, { status: 400 });
  }

  const params = new URLSearchParams({ lat, lng });
  for (const key of ["radius_km", "category", "mode"]) {
    const value = incoming.get(key);
    if (value) params.set(key, value);
  }

  const cookieHeader = (await cookies()).toString();
  const authHeaders: Record<string, string> = cookieHeader ? { Cookie: cookieHeader } : {};

  // Primary: token from Django → FastAPI read service.
  try {
    const tokRes = await fetch(`${BACKEND_URL}/api/auth/search-token/`, {
      headers: authHeaders,
      cache: "no-store",
    });
    if (tokRes.ok) {
      const { token } = (await tokRes.json()) as { token: string };
      const searchRes = await fetch(`${SEARCH_URL}/search/providers?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
        cache: "no-store",
      });
      if (searchRes.ok) {
        const data = (await searchRes.json()) as { results: SearchRow[] };
        return NextResponse.json({ source: "search-service", results: data.results });
      }
    }
  } catch {
    // Search service down / unreachable — fall through to Django.
  }

  // Fallback: Django's own search endpoint (public), shape normalised.
  const djangoRes = await fetch(`${BACKEND_URL}/api/providers/search/?${params}`, {
    headers: authHeaders,
    cache: "no-store",
  });
  if (!djangoRes.ok) {
    const body = await djangoRes.text();
    return new NextResponse(body, {
      status: djangoRes.status,
      headers: { "Content-Type": djangoRes.headers.get("content-type") ?? "application/json" },
    });
  }
  const rows = (await djangoRes.json()) as DjangoRow[];
  const results: SearchRow[] = rows.map((p) => ({
    id: p.id,
    full_name: p.full_name,
    bio: p.bio,
    rating_avg: Number(p.rating_avg),
    rating_count: p.rating_count,
    distance_km: p.distance_km,
  }));
  return NextResponse.json({ source: "django", results });
}
