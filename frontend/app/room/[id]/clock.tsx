"use client";

import { useEffect, useState } from "react";
import type { View } from "../../lib";
import type { Link } from "../../live";
import type { Send } from "./terminal";

const SPEEDS = [1, 2, 4] as const;
const LINK: Record<Link, string> = {
  connecting: "Connecting…", live: "Live", reconnecting: "Reconnecting… (polling meanwhile)", polling: "Polling",
};

/** Timed rounds: the server's real-time clock advances one execution window when the countdown ends, unless a
 *  partner pauses. It auto-pauses on new notices, alerts and unsigned packages; every tick is a logged command. */
export function Clock({ v, send, link }: { v: View; send: Send; link: Link }) {
  const rt = v.realtime;
  const [left, setLeft] = useState(rt.next_tick_in);
  useEffect(() => {
    const until = Date.now() + rt.next_tick_in * 1000;
    setLeft(rt.next_tick_in);
    const t = setInterval(() => setLeft(Math.max(0, (until - Date.now()) / 1000)), 250);
    return () => clearInterval(t);
  }, [rt.next_tick_in, rt.next_tick_at]);

  if (v.clock.finished) return null;
  const reason = v.clock_state?.reason;
  return (
    <div className="tw:grid tw:gap-2" aria-label="Round timer">
      <p role="status">
        {rt.running
          ? <>Round timer {rt.speed}x: next window in <strong className="tw:font-mono">{Math.ceil(left)} s</strong></>
          : <>Timer paused{reason ? `: ${reason}` : ""}</>}
        <span className="muted"> · {LINK[link]}</span>
      </p>
      <div className="tw:flex tw:flex-wrap tw:gap-2">
        {SPEEDS.map((s) => (
          <button key={s} type="button" className="secondary" aria-pressed={rt.running && rt.speed === s}
                  onClick={() => send({ type: "set_speed", speed: s }, `Timer running at ${s}x.`)}>
            {s === 1 ? "Start timer 1x" : `${s}x`}
          </button>
        ))}
        <button type="button" className="secondary" disabled={!rt.running} onClick={() => send({ type: "pause" }, "Timer paused.")}>
          Pause
        </button>
      </div>
    </div>
  );
}
