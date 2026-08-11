"use client";

import "leaflet/dist/leaflet.css";

import L from "leaflet";
import { useEffect } from "react";
import { MapContainer, Marker, TileLayer, useMap, useMapEvents } from "react-leaflet";

export type Coords = { lat: number; lng: number };

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

// Recenters only when `trigger` changes — i.e. when the pin is set from OUTSIDE
// the map (the "use my location" button), not on every map click, which would
// make the view jump while the user is placing the pin by hand.
function Recenter({ coords, trigger }: { coords: Coords | null; trigger: number }) {
  const map = useMap();
  useEffect(() => {
    if (coords) map.setView([coords.lat, coords.lng], 14);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [trigger]);
  return null;
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
  const center = value ? ([value.lat, value.lng] as [number, number]) : DEFAULT_CENTER;
  return (
    <div className="h-72 w-full overflow-hidden rounded-lg border border-neutral-300 dark:border-neutral-700">
      <MapContainer center={center} zoom={value ? 14 : 4} scrollWheelZoom className="h-full w-full">
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <ClickToPlace onPick={onChange} />
        <Recenter coords={value} trigger={recenterKey} />
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
  );
}
