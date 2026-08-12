import { cookies } from "next/headers";
import { NextResponse } from "next/server";

// Place search (and reverse lookup) for the map picker, proxied server-side.
//
// Two reasons this doesn't run in the browser:
//  1. Consistency with the BFF — the browser talks to our origin only.
//  2. Nominatim's usage policy requires a User-Agent identifying the app and
//     caps callers at ~1 req/sec. We can only honour both from the server, where
//     we also cache and throttle centrally rather than per browser tab.
//
// GET /api/geocode?q=koramangala          → { results: [{ label, lat, lng, bbox }] }
// GET /api/geocode?lat=12.9&lng=77.6      → { label }  (reverse)

const NOMINATIM = "https://nominatim.openstreetmap.org";
const USER_AGENT = "workisto/1.0 (portfolio demo; https://github.com/Jain-Paul-9933/workisto)";

// Nominatim asks for no more than one request a second. Requests queue behind
// this promise chain so we stay polite even with several tabs typing at once.
const MIN_INTERVAL_MS = 1100;
let lastCall = 0;
let queue: Promise<unknown> = Promise.resolve();

function scheduled<T>(task: () => Promise<T>): Promise<T> {
  const run = queue.then(async () => {
    const wait = lastCall + MIN_INTERVAL_MS - Date.now();
    if (wait > 0) await new Promise((r) => setTimeout(r, wait));
    lastCall = Date.now();
    return task();
  });
  // Keep the chain alive even if this task rejects.
  queue = run.then(
    () => undefined,
    () => undefined,
  );
  return run;
}

// Small bounded cache — the same place names repeat a lot while someone types,
// and the usage policy explicitly asks callers to cache.
const cache = new Map<string, unknown>();
const CACHE_MAX = 200;

async function cached<T>(key: string, task: () => Promise<T>): Promise<T> {
  const hit = cache.get(key);
  if (hit !== undefined) return hit as T;
  const value = await task();
  if (cache.size >= CACHE_MAX) cache.delete(cache.keys().next().value as string);
  cache.set(key, value);
  return value;
}

type NominatimPlace = {
  display_name: string;
  lat: string;
  lon: string;
  boundingbox?: [string, string, string, string]; // south, north, west, east
};

export type Place = {
  label: string;
  lat: number;
  lng: number;
  // [[south, west], [north, east]] — the shape Leaflet's fitBounds wants.
  bbox: [[number, number], [number, number]] | null;
};

function toPlace(p: NominatimPlace): Place {
  const bb = p.boundingbox;
  return {
    label: p.display_name,
    lat: Number(p.lat),
    lng: Number(p.lon),
    bbox: bb
      ? [
          [Number(bb[0]), Number(bb[2])],
          [Number(bb[1]), Number(bb[3])],
        ]
      : null,
  };
}

async function callNominatim(path: string) {
  const res = await fetch(`${NOMINATIM}${path}`, {
    headers: { "User-Agent": USER_AGENT, "Accept-Language": "en" },
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`geocoder returned ${res.status}`);
  return res.json();
}

export async function GET(req: Request) {
  // Both callers (onboarding, customer search) sit behind login, and the shared
  // 1 req/sec budget is easy to starve — so don't leave this open as a free
  // geocoding proxy. Presence of a session is enough of a gate here; this
  // endpoint returns public map data and Django remains the real authority.
  if (!(await cookies()).has("sessionid")) {
    return NextResponse.json({ detail: "Authentication required.", results: [] }, { status: 401 });
  }

  const params = new URL(req.url).searchParams;
  const q = params.get("q")?.trim();
  const lat = params.get("lat");
  const lng = params.get("lng");

  try {
    // Reverse: coordinates → a human-readable label for the dropped pin.
    if (lat && lng) {
      const key = `r:${Number(lat).toFixed(4)},${Number(lng).toFixed(4)}`;
      const label = await cached(key, async () => {
        const data = (await scheduled(() =>
          callNominatim(`/reverse?lat=${lat}&lon=${lng}&format=jsonv2&zoom=16`),
        )) as { display_name?: string };
        return data.display_name ?? "";
      });
      return NextResponse.json({ label });
    }

    // Forward: free-text place search.
    if (!q || q.length < 3) return NextResponse.json({ results: [] });

    const key = `s:${q.toLowerCase()}`;
    const results = await cached(key, async () => {
      const data = (await scheduled(() =>
        callNominatim(`/search?q=${encodeURIComponent(q)}&format=jsonv2&limit=6&addressdetails=0`),
      )) as NominatimPlace[];
      return data.map(toPlace);
    });
    return NextResponse.json({ results });
  } catch {
    // The picker degrades to tap-the-map when this is unavailable.
    return NextResponse.json(
      { detail: "Place search is unavailable.", results: [] },
      { status: 503 },
    );
  }
}
