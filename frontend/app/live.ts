"use client";

import { useEffect, useRef, useState } from "react";

export type Link = "connecting" | "live" | "reconnecting" | "polling";

const UNAUTHORIZED = 4401; // fundforge.presence close codes: retrying cannot help
const TOO_MANY = 4429;

/** Where the presence socket lives. Same origin by default (Next proxies it locally and Caddy does in the VM
 *  stack); on Vercel, which cannot proxy WebSockets, NEXT_PUBLIC_API_ORIGIN names the API host instead. */
export function socketUrl(roomId: string, origin: string, apiOrigin = process.env.NEXT_PUBLIC_API_ORIGIN ?? ""): string {
  const base = (apiOrigin || origin).replace(/^http/, "ws").replace(/\/$/, "");
  return `${base}/api/rooms/${encodeURIComponent(roomId)}/presence`;
}

/** Reconnect delay: 1 s doubling to 30 s, with up to 30% jitter so many clients do not retry in step. */
export function backoff(attempt: number, random = Math.random): number {
  const base = Math.min(30_000, 1000 * 2 ** attempt);
  return Math.round(base * (1 + 0.3 * random()));
}

/** Subscribe to "the room changed" nudges and call `onNudge` for each. The socket is only a latency shortcut:
 *  the desk keeps polling, so a dropped socket costs speed, never state. Reconnects with backoff forever,
 *  except when the server refuses the seat. */
export function useRoomSocket(roomId: string, token: string | null, onNudge: () => void): Link {
  const [link, setLink] = useState<Link>("connecting");
  const nudge = useRef(onNudge);
  nudge.current = onNudge;

  useEffect(() => {
    if (!token || typeof WebSocket === "undefined") return;
    let ws: WebSocket | null = null;
    let timer: ReturnType<typeof setTimeout> | undefined;
    let attempt = 0;
    let stopped = false;
    let refused = false; // 4401/4429: the server will not take this seat again, so never reconnect

    const open = () => {
      ws = new WebSocket(socketUrl(roomId, window.location.origin));
      ws.onopen = () => ws?.send(JSON.stringify({ type: "hello", token }));
      ws.onmessage = (m) => {
        const msg = JSON.parse(String(m.data));
        if (msg.type === "welcome") {
          attempt = 0;
          setLink("live");
          nudge.current(); // catch up on anything missed while disconnected
        } else if (msg.type === "version") {
          nudge.current();
        }
      };
      ws.onclose = (e) => {
        if (stopped) return;
        if (e.code === UNAUTHORIZED || e.code === TOO_MANY) {
          refused = true;
          setLink("polling");
          return;
        }
        setLink("reconnecting");
        timer = setTimeout(open, backoff(attempt++));
      };
    };
    const wake = () => { // back online or back on the tab: retry now instead of waiting out the backoff
      if (!refused && !stopped && ws?.readyState === WebSocket.CLOSED) {
        clearTimeout(timer); // keep `attempt`: tab switches must not reset the backoff
        open();
      }
      nudge.current();
    };
    open();
    window.addEventListener("online", wake);
    document.addEventListener("visibilitychange", wake);
    return () => {
      stopped = true;
      clearTimeout(timer);
      window.removeEventListener("online", wake);
      document.removeEventListener("visibilitychange", wake);
      ws?.close();
    };
  }, [roomId, token]);

  return link;
}
