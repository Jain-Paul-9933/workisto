"use client";

import dynamic from "next/dynamic";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button, ErrorText, Field, Input, Textarea } from "@/components/ui";
import { apiSend } from "@/lib/api-client";
import { firstError } from "@/lib/errors";
import type { Provider } from "@/lib/types";
import type { Coords } from "./map-picker";

// The map touches `window`/Leaflet, so it's client-only — loaded lazily with a
// placeholder while its JS arrives. (`ssr: false` is only allowed inside a
// Client Component, which this is.)
const MapPicker = dynamic(() => import("./map-picker"), {
  ssr: false,
  loading: () => (
    <div className="flex h-72 w-full items-center justify-center rounded-lg border border-neutral-300 text-sm text-neutral-500 dark:border-neutral-700">
      Loading map…
    </div>
  ),
});

export default function OnboardingForm({ initial }: { initial: Provider | null }) {
  const router = useRouter();
  const editing = initial !== null;

  const [fullName, setFullName] = useState(initial?.full_name ?? "");
  const [bio, setBio] = useState(initial?.bio ?? "");
  const [radius, setRadius] = useState(initial?.service_radius_km ?? "5");
  const [coords, setCoords] = useState<Coords | null>(
    initial?.location
      ? { lat: initial.location.latitude, lng: initial.location.longitude }
      : null,
  );
  const [recenterKey, setRecenterKey] = useState(0);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  // Pin updates from outside the map (geolocation) bump recenterKey so the map
  // pans to them; map clicks/drags set coords directly and leave the view be.
  function setFromOutside(c: Coords) {
    setCoords(c);
    setRecenterKey((k) => k + 1);
  }

  function useMyLocation() {
    setError("");
    if (!("geolocation" in navigator)) {
      setError("This browser can't share your location — tap the map or type coordinates.");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => setFromOutside({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
      () => setError("Couldn't read your location — tap the map to drop a pin instead."),
    );
  }

  function setManual(part: "lat" | "lng", raw: string) {
    const n = Number(raw);
    if (raw !== "" && Number.isNaN(n)) return;
    const base = coords ?? { lat: 0, lng: 0 };
    setCoords(part === "lat" ? { ...base, lat: n } : { ...base, lng: n });
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (!coords) {
      setError("Drop a pin on the map so customers nearby can find you.");
      return;
    }
    setSaving(true);
    const payload = {
      full_name: fullName,
      bio,
      service_radius_km: radius,
      latitude: coords.lat,
      longitude: coords.lng,
    };
    const res = editing
      ? await apiSend("/providers/me", "PATCH", payload)
      : await apiSend("/providers", "POST", payload);
    setSaving(false);
    if (res.ok) {
      router.replace("/dashboard");
      router.refresh();
      return;
    }
    const data = await res.json().catch(() => null);
    setError(firstError(data, "Couldn't save your profile. Please try again."));
  }

  return (
    <form onSubmit={onSubmit} className="space-y-5">
      <Field label="Full name">
        <Input
          required
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          placeholder="e.g. Ramesh Kumar"
        />
      </Field>

      <Field label="About your work (optional)">
        <Textarea
          rows={3}
          value={bio}
          onChange={(e) => setBio(e.target.value)}
          placeholder="What you do, your experience, anything customers should know."
        />
      </Field>

      <Field label="How far will you travel? (km)">
        <Input
          type="number"
          min="0"
          step="0.5"
          required
          value={radius}
          onChange={(e) => setRadius(e.target.value)}
        />
      </Field>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-neutral-700 dark:text-neutral-300">
            Your location
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
        <p className="text-xs text-neutral-500">
          Tap the map or drag the pin to mark exactly where you&rsquo;re based.
        </p>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Latitude">
            <Input
              inputMode="decimal"
              value={coords ? String(coords.lat) : ""}
              onChange={(e) => setManual("lat", e.target.value)}
              placeholder="—"
            />
          </Field>
          <Field label="Longitude">
            <Input
              inputMode="decimal"
              value={coords ? String(coords.lng) : ""}
              onChange={(e) => setManual("lng", e.target.value)}
              placeholder="—"
            />
          </Field>
        </div>
      </div>

      <ErrorText>{error}</ErrorText>
      <Button type="submit" disabled={saving}>
        {saving ? "Saving…" : editing ? "Save changes" : "Complete onboarding"}
      </Button>
    </form>
  );
}
