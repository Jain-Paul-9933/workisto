"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useEffect, useState } from "react";

import { Badge, Button, Field, Input, Select } from "@/components/ui";
import { apiGet } from "@/lib/api-client";
import type { Category, SearchResult, ServiceMode } from "@/lib/types";
import type { Coords } from "@/components/map-picker";

const MapPicker = dynamic(() => import("@/components/map-picker"), {
  ssr: false,
  loading: () => (
    <div className="flex h-72 w-full items-center justify-center rounded-lg border border-neutral-300 text-sm text-neutral-500 dark:border-neutral-700">
      Loading map…
    </div>
  ),
});

export default function SearchClient() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [coords, setCoords] = useState<Coords | null>(null);
  const [recenterKey, setRecenterKey] = useState(0);
  const [category, setCategory] = useState("");
  const [mode, setMode] = useState<"" | ServiceMode>("");
  const [radius, setRadius] = useState("10");

  const [results, setResults] = useState<SearchResult[] | null>(null);
  const [source, setSource] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    apiGet("/categories")
      .then((r) => (r.ok ? r.json() : []))
      .then(setCategories)
      .catch(() => setCategories([]));
  }, []);

  function useMyLocation() {
    setError("");
    if (!("geolocation" in navigator)) {
      setError("This browser can't share your location — tap the map to set where to search.");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setCoords({ lat: pos.coords.latitude, lng: pos.coords.longitude });
        setRecenterKey((k) => k + 1);
      },
      () => setError("Couldn't read your location — tap the map to set a search point instead."),
    );
  }

  async function search(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (!coords) {
      setError("Set where to search — use your location or tap the map.");
      return;
    }
    setLoading(true);
    const params = new URLSearchParams({
      lat: String(coords.lat),
      lng: String(coords.lng),
      radius_km: radius,
    });
    if (category) params.set("category", category);
    if (mode) params.set("mode", mode);

    const res = await fetch(`/api/search?${params}`, { credentials: "same-origin" });
    setLoading(false);
    if (!res.ok) {
      setError("Search failed. Please try again.");
      return;
    }
    const data = await res.json();
    setResults(data.results);
    setSource(data.source);
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Find a provider near you</h1>
        <p className="mt-1 text-sm text-neutral-500">
          Set a location, then filter by service. Ranked by rating, then distance.
        </p>
      </div>

      <form onSubmit={search} className="space-y-4 rounded-xl border border-neutral-200 bg-white p-5 dark:border-neutral-800 dark:bg-neutral-900">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-neutral-700 dark:text-neutral-300">
            Where to look
          </span>
          <button
            type="button"
            onClick={useMyLocation}
            className="text-sm font-medium text-indigo-600 hover:underline"
          >
            Use my current location
          </button>
        </div>
        <MapPicker value={coords} onChange={setCoords} recenterKey={recenterKey} />

        <div className="grid gap-3 sm:grid-cols-3">
          <Field label="Service">
            <Select value={category} onChange={(e) => setCategory(e.target.value)}>
              <option value="">Any service</option>
              {categories.map((c) => (
                <option key={c.id} value={c.slug}>
                  {c.name}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Mode">
            <Select value={mode} onChange={(e) => setMode(e.target.value as "" | ServiceMode)}>
              <option value="">Any mode</option>
              <option value="ONSITE">On-site</option>
              <option value="CHAT">Chat</option>
            </Select>
          </Field>
          <Field label="Radius (km)">
            <Input
              type="number"
              min="1"
              max="50"
              value={radius}
              onChange={(e) => setRadius(e.target.value)}
            />
          </Field>
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}
        <Button type="submit" disabled={loading} className="w-auto px-6">
          {loading ? "Searching…" : "Search"}
        </Button>
      </form>

      {results !== null && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">
              {results.length} {results.length === 1 ? "provider" : "providers"} found
            </h2>
            {source && (
              <span className="text-xs text-neutral-400">
                via {source === "search-service" ? "search service" : "Django"}
              </span>
            )}
          </div>

          {results.length === 0 ? (
            <p className="text-sm text-neutral-500">
              No providers matched. Try a wider radius or a different service.
            </p>
          ) : (
            <ul className="space-y-3">
              {results.map((p) => (
                <li key={p.id}>
                  <Link
                    href={`/providers/${p.id}`}
                    className="block rounded-xl border border-neutral-200 bg-white p-5 transition hover:border-indigo-300 hover:shadow-sm dark:border-neutral-800 dark:bg-neutral-900 dark:hover:border-indigo-700"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="font-medium">{p.full_name}</p>
                        {p.bio && (
                          <p className="mt-1 line-clamp-2 max-w-lg text-sm text-neutral-500">
                            {p.bio}
                          </p>
                        )}
                      </div>
                      <div className="text-right text-sm">
                        <Badge tone="indigo">{p.distance_km} km</Badge>
                        <p className="mt-1 text-neutral-500">
                          {p.rating_count > 0
                            ? `★ ${p.rating_avg.toFixed(2)} (${p.rating_count})`
                            : "No reviews yet"}
                        </p>
                      </div>
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
