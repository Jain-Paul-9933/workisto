"use client";

import "leaflet/dist/leaflet.css";

import L from "leaflet";
import { useCallback, useEffect, useRef, useState } from "react";
import { MapContainer, Marker, TileLayer, useMap, useMapEvents } from "react-leaflet";

export type Coords = { lat: number; lng: number };
type Bounds = [[number, number], [number, number]];
type Place = { label: string; lat: number; lng: number; bbox: Bounds | null };

// Rough centroid of India — a sensible default view before a pin is dropped.
const DEFAULT_CENTER: [number, number] = [20.5937, 78.9629];

// A self-contained SVG pin (indigo, matching the app theme). Using a divIcon
// sidesteps Leaflet's bundled PNG marker assets, which break under bundlers
// unless specially configured — nothing external to load.
const pinIcon = L.divIcon({
  className: "workisto-pin",
  html: `
    <svg width="28" height="38" viewBox="0 0 28 38" xmlns="http://www.w3.org/2000/svg">
      <path d="M14 0C6.27 0 0 6.27 0 14c0 10.5 14 24 14 24s14-13.5 14-24C28 6.27 21.73 0 14 0z" fill="#4f46e5"/>
      <circle cx="14" cy="14" r="5.5" fill="#ffffff"/>
    </svg>`,
  iconSize: [28, 38],
  iconAnchor: [14, 38],
});

function ClickToPlace({ onPick }: { onPick: (c: Coords) => void }) {
  useMapEvents({
    click(e) {
      onPick({ lat: e.latlng.lat, lng: e.latlng.lng });
    },
  });
  return null;
}

// Moves the view only when `target` is replaced — i.e. when the pin is set from
// outside the map (search result, "use my location"), never on a plain map click,
// which would make the view jump while someone is placing the pin by hand.
// A searched place carries its bounding box, so a city zooms out and a street
// zooms in, instead of every result landing on the same arbitrary zoom.
function Recenter({ target }: { target: { c: Coords; bbox: Bounds | null } | null }) {
  const map = useMap();
  useEffect(() => {
    if (!target) return;
    if (target.bbox) map.fitBounds(target.bbox, { maxZoom: 16 });
    else map.setView([target.c.lat, target.c.lng], 15);
  }, [target, map]);
  return null;
}

function PlaceSearch({ onPick }: { onPick: (p: Place) => void }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Place[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [highlight, setHighlight] = useState(0);
  const [error, setError] = useState("");

  useEffect(() => {
    const q = query.trim();
    if (q.length < 3) {
      setResults([]);
      setError("");
      return;
    }
    // Debounced so we search when typing pauses, not on every keystroke.
    const controller = new AbortController();
    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const res = await fetch(`/api/geocode?q=${encodeURIComponent(q)}`, {
          signal: controller.signal,
        });
        const data = await res.json();
        setResults(data.results ?? []);
        setHighlight(0);
        setOpen(true);
        setError(res.ok ? "" : (data.detail ?? "Place search is unavailable."));
      } catch (err) {
        if ((err as Error).name !== "AbortError") setError("Place search is unavailable.");
      } finally {
        setLoading(false);
      }
    }, 450);

    return () => {
      controller.abort();
      clearTimeout(timer);
    };
  }, [query]);

  function choose(place: Place) {
    onPick(place);
    setQuery(place.label);
    setOpen(false);
    setResults([]);
  }

  function onKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Escape") return setOpen(false);
    if (!open || results.length === 0) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setHighlight((h) => (h + 1) % results.length);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setHighlight((h) => (h - 1 + results.length) % results.length);
    } else if (e.key === "Enter") {
      e.preventDefault(); // don't submit the surrounding form
      choose(results[highlight]);
    }
  }

  return (
    <div className="relative">
      <div className="relative">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={onKeyDown}
          onFocus={() => results.length > 0 && setOpen(true)}
          onBlur={() => setOpen(false)}
          placeholder="Search a place — area, landmark, or address"
          aria-label="Search for a place"
          className="w-full rounded-lg border border-neutral-300 bg-white py-2 pl-9 pr-3 text-sm text-neutral-900 outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-100"
        />
        <svg
          className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-neutral-400"
          viewBox="0 0 20 20"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <circle cx="9" cy="9" r="6" />
          <path d="M14 14l4 4" strokeLinecap="round" />
        </svg>
        {loading && (
          <span className="absolute right-3 top-2.5 text-xs text-neutral-400">searching…</span>
        )}
      </div>

      {open && results.length > 0 && (
        // Above Leaflet's control panes (which go up to z-index 1000).
        <ul
          // Keep mousedown from blurring the input before the click registers.
          onMouseDown={(e) => e.preventDefault()}
          className="absolute z-[1200] mt-1 max-h-56 w-full overflow-y-auto rounded-lg border border-neutral-200 bg-white shadow-lg dark:border-neutral-700 dark:bg-neutral-900"
        >
          {results.map((r, i) => (
            <li key={`${r.lat},${r.lng},${i}`}>
              <button
                type="button"
                onClick={() => choose(r)}
                onMouseEnter={() => setHighlight(i)}
                className={
                  "block w-full px-3 py-2 text-left text-sm transition " +
                  (i === highlight
                    ? "bg-indigo-50 text-indigo-900 dark:bg-indigo-950/50 dark:text-indigo-100"
                    : "text-neutral-700 dark:text-neutral-300")
                }
              >
                {r.label}
              </button>
            </li>
          ))}
        </ul>
      )}

      {error && <p className="mt-1 text-xs text-amber-600">{error} Tap the map instead.</p>}
    </div>
  );
}

export default function MapPicker({
  value,
  onChange,
  recenterKey = 0,
}: {
  value: Coords | null;
  onChange: (c: Coords) => void;
  recenterKey?: number;
}) {
  const [target, setTarget] = useState<{ c: Coords; bbox: Bounds | null } | null>(null);
  const [label, setLabel] = useState("");
  // Remembers the label of a place chosen from search, so we don't reverse-
  // geocode coordinates whose name we already know.
  const known = useRef<{ lat: number; lng: number; label: string } | null>(null);

  // The parent bumps recenterKey when it sets the pin itself ("use my location").
  useEffect(() => {
    if (recenterKey > 0 && value) setTarget({ c: value, bbox: null });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [recenterKey]);

  const pickPlace = useCallback(
    (p: Place) => {
      const c = { lat: p.lat, lng: p.lng };
      known.current = { ...c, label: p.label };
      setLabel(p.label);
      onChange(c);
      setTarget({ c, bbox: p.bbox });
    },
    [onChange],
  );

  // Name whatever the pin is currently on, so the choice is legible without
  // anyone reading coordinates. Debounced — dragging shouldn't spam the API.
  useEffect(() => {
    if (!value) {
      setLabel("");
      return;
    }
    const k = known.current;
    if (k && Math.abs(k.lat - value.lat) < 1e-6 && Math.abs(k.lng - value.lng) < 1e-6) {
      setLabel(k.label);
      return;
    }
    const controller = new AbortController();
    const timer = setTimeout(async () => {
      try {
        const res = await fetch(`/api/geocode?lat=${value.lat}&lng=${value.lng}`, {
          signal: controller.signal,
        });
        const data = await res.json();
        if (data.label) setLabel(data.label);
      } catch {
        /* label is a nicety; the coordinates are what actually matter */
      }
    }, 700);
    return () => {
      controller.abort();
      clearTimeout(timer);
    };
  }, [value?.lat, value?.lng]);

  const center = value ? ([value.lat, value.lng] as [number, number]) : DEFAULT_CENTER;

  return (
    <div className="space-y-2">
      <PlaceSearch onPick={pickPlace} />

      <div className="h-72 w-full overflow-hidden rounded-lg border border-neutral-300 dark:border-neutral-700">
        <MapContainer
          center={center}
          zoom={value ? 15 : 4}
          scrollWheelZoom
          className="h-full w-full"
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <ClickToPlace onPick={onChange} />
          <Recenter target={target} />
          {value && (
            <Marker
              position={[value.lat, value.lng]}
              icon={pinIcon}
              draggable
              eventHandlers={{
                dragend(e) {
                  const p = (e.target as L.Marker).getLatLng();
                  onChange({ lat: p.lat, lng: p.lng });
                },
              }}
            />
          )}
        </MapContainer>
      </div>

      {value && (
        <p className="text-xs text-neutral-500">
          <span className="font-medium text-neutral-700 dark:text-neutral-300">Selected:</span>{" "}
          {label || `${value.lat.toFixed(5)}, ${value.lng.toFixed(5)}`}
        </p>
      )}
    </div>
  );
}
