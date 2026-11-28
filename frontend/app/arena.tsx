"use client";

import { useEffect, useRef, useState } from "react";
import { exclusive } from "./exclusive";
import { call } from "./account";
import type { NewRoom } from "./lib";

type Invite = { code: string; role: string };
type Joined = { room_id: string; role: string; token: string };

const seatUrl = (room: string, token: string) => `/room/${room}#t=${token}`;

/** The three ways in: solo against the bot in one click, host a co-op room with a join code, or join with one. */
export function Arena() {
  const [hosted, setHosted] = useState<{ room: string; token: string; code: string } | null>(null);
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const inFlight = useRef(false); // one room per click, even on a double-click

  useEffect(() => {
    const given = new URLSearchParams(window.location.search).get("join");
    if (given) setCode(given.toUpperCase());
  }, []);

  const run = (what: string, f: () => Promise<void>) =>
    void exclusive(inFlight, async () => {
      setBusy(true);
      setError("");
      try {
        await f();
      } catch (err) {
        setError(`Couldn't ${what}: ${(err as Error).message}`);
      } finally {
        setBusy(false);
      }
    });

  const solo = () => run("start a solo game", async () => {
    const r = await call<NewRoom>("/api/rooms", { body: { scenario: "case1", pm_name: "You", solo_role: "pm" } });
    window.location.assign(seatUrl(r.room_id, r.tokens.pm));
  });

  const host = () => run("open a co-op room", async () => {
    const r = await call<NewRoom>("/api/rooms", { body: { scenario: "case1", pm_name: "Host", mp_name: "Guest" } });
    const inv = await call<Invite>(`/api/rooms/${r.room_id}/invite`, { body: {}, seat: r.tokens.pm });
    setHosted({ room: r.room_id, token: r.tokens.pm, code: inv.code });
  });

  const join = (e: React.FormEvent) => {
    e.preventDefault();
    run("join", async () => {
      const j = await call<Joined>("/api/join", { body: { code } });
      window.location.assign(seatUrl(j.room_id, j.token));
    });
  };

  return (
    <section aria-labelledby="arena-title" className="tw:grid tw:gap-4 tw:rounded-lg tw:border tw:border-[var(--rule)] tw:bg-[var(--sheet)] tw:p-5">
      <h2 id="arena-title" className="tw:text-xl">Play now</h2>
      <div className="tw:grid tw:gap-4 tw:md:grid-cols-3">
        <div className="tw:grid tw:content-start tw:gap-2">
          <p className="tw:text-[var(--ink-soft)]">You trade; a rules-based bot partner runs operations. No sign-up.</p>
          <button type="button" onClick={solo} disabled={busy} className="tw:justify-self-start tw:px-4 tw:py-2">Play solo</button>
        </div>

        <div className="tw:grid tw:content-start tw:gap-2">
          <p className="tw:text-[var(--ink-soft)]">Host a two-player fund and send your partner a six-letter code.</p>
          {!hosted ? (
            <button type="button" onClick={host} disabled={busy} className="tw:justify-self-start tw:px-4 tw:py-2">Host co-op</button>
          ) : (
            <div className="tw:grid tw:gap-2" aria-live="polite">
              <p>Join code <strong className="tw:font-mono tw:text-2xl tw:tracking-widest" data-testid="join-code">{hosted.code}</strong></p>
              <p className="tw:text-sm tw:text-[var(--ink-soft)]">Single use, valid 24 hours. Your partner enters it under Join.</p>
              <a href={seatUrl(hosted.room, hosted.token)}>Enter as portfolio manager</a>
            </div>
          )}
        </div>

        <form onSubmit={join} className="tw:grid tw:content-start tw:gap-2">
          <label className="tw:grid tw:gap-1">
            Join code
            <input value={code} onChange={(e) => setCode(e.target.value.toUpperCase())} maxLength={16}
                   autoComplete="off" spellCheck={false} placeholder="ABC123" className="tw:font-mono tw:tracking-widest" />
          </label>
          <button type="submit" disabled={busy || !code.trim()} className="tw:justify-self-start tw:px-4 tw:py-2">Join</button>
        </form>
      </div>
      {error && <p className="error" role="alert">{error}</p>}
    </section>
  );
}
