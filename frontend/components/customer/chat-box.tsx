"use client";

import { useEffect, useRef, useState } from "react";

import { apiGet } from "@/lib/api-client";
import type { ChatMessage } from "@/lib/types";

// The chat WebSocket connects straight to Django's ASGI server (Channels), not
// through the BFF — Next doesn't proxy sockets. It authenticates by the session
// cookie riding the handshake: the frontend and Django are same-site (both
// localhost in dev), so the cookie is sent and AuthMiddlewareStack resolves the
// user (ADR 0001). Behind a single domain in prod this is same-origin; override
// the base with NEXT_PUBLIC_WS_URL if the socket lives elsewhere.
const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";

type Line = { id: number; sender_id: number; sender: string; body: string; at: string };

export default function ChatBox({ bookingId, meId }: { bookingId: number; meId: number }) {
  const [lines, setLines] = useState<Line[]>([]);
  const [draft, setDraft] = useState("");
  const [connected, setConnected] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);
  const endRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    let closed = false;

    // Load history over HTTP first, then let the live socket take over.
    apiGet(`/bookings/${bookingId}/messages`)
      .then((r) => (r.ok ? r.json() : []))
      .then((history: ChatMessage[]) => {
        if (closed) return;
        setLines(
          history.map((m) => ({
            id: m.id,
            sender_id: m.sender,
            sender: m.sender_email,
            body: m.body,
            at: m.created_at,
          })),
        );
      })
      .catch(() => {});

    const ws = new WebSocket(`${WS_BASE}/ws/bookings/${bookingId}/chat/`);
    socketRef.current = ws;
    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onmessage = (event) => {
      const d = JSON.parse(event.data);
      setLines((cur) =>
        cur.some((l) => l.id === d.id)
          ? cur
          : [...cur, { id: d.id, sender_id: d.sender_id, sender: d.sender, body: d.message, at: d.created_at }],
      );
    };

    return () => {
      closed = true;
      ws.close();
    };
  }, [bookingId]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [lines]);

  function send(e: React.FormEvent) {
    e.preventDefault();
    const body = draft.trim();
    if (!body || socketRef.current?.readyState !== WebSocket.OPEN) return;
    socketRef.current.send(JSON.stringify({ message: body }));
    setDraft("");
  }

  return (
    <div className="rounded-xl border border-neutral-200 dark:border-neutral-800">
      <div className="h-64 space-y-2 overflow-y-auto p-4">
        {lines.length === 0 ? (
          <p className="text-sm text-neutral-400">No messages yet. Say hello.</p>
        ) : (
          lines.map((l) => {
            const mine = l.sender_id === meId;
            return (
              <div key={l.id} className={mine ? "text-right" : "text-left"}>
                <div
                  className={
                    "inline-block max-w-[75%] rounded-2xl px-3 py-1.5 text-sm " +
                    (mine
                      ? "bg-indigo-600 text-white"
                      : "bg-neutral-100 text-neutral-800 dark:bg-neutral-800 dark:text-neutral-100")
                  }
                >
                  {l.body}
                </div>
              </div>
            );
          })
        )}
        <div ref={endRef} />
      </div>
      <form onSubmit={send} className="flex gap-2 border-t border-neutral-200 p-3 dark:border-neutral-800">
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder={connected ? "Type a message…" : "Connecting…"}
          className="flex-1 rounded-lg border border-neutral-300 bg-white px-3 py-2 text-sm outline-none focus:border-indigo-500 dark:border-neutral-700 dark:bg-neutral-900"
        />
        <button
          type="submit"
          disabled={!connected || !draft.trim()}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-60"
        >
          Send
        </button>
      </form>
    </div>
  );
}
