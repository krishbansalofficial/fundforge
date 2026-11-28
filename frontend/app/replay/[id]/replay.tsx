"use client";

import { useEffect, useState } from "react";
import { call, type ResultDetail, type Reverify } from "../../account";
import { Nav } from "../../nav";

const ACTOR: Record<string, string> = { pm: "Portfolio manager", mp: "Managing partner", clock: "Clock" };

/** A ranked room's public record: outcome, journal digest, every command in order, and a live re-verification. */
export function Replay({ roomId }: { roomId: string }) {
  const [r, setR] = useState<ResultDetail | null>(null);
  const [check, setCheck] = useState<Reverify | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    call<ResultDetail>(`/api/results/${roomId}`).then(setR).catch((e: Error) => setError(e.message));
  }, [roomId]);

  const verify = () =>
    call<Reverify>(`/api/results/${roomId}/verify`, { body: {} }).then(setCheck).catch((e: Error) => setError(e.message));

  return (
    <main className="landing">
      <Nav />
      <h1>Replay {roomId}</h1>
      {error && <p className="error" role="alert">{error}</p>}
      {r && <>
        <p className="lede">
          {r.players.pm} &amp; {r.players.mp}: <strong>{r.label}</strong>, score {Number(r.score).toFixed(2)}, scenario {r.scenario}, rules {r.rules_version}.
        </p>
        <p className="digest">Journal digest {r.journal_digest}</p>
        <div className="tw:flex tw:flex-wrap tw:items-center tw:gap-3">
          <button type="button" onClick={verify}>Replay and verify now</button>
          {check && <span role="status">{check.ok && check.matches_recorded
            ? "Verified: the command log replays to the same journal digest."
            : `Verification failed: ${check.error ?? "digest differs from the recorded one"}`}</span>}
        </div>
        <h2>Decisions, in order</h2>
        <table>
          <thead><tr><th scope="col" className="n">#</th><th scope="col">Actor</th><th scope="col">Command</th><th scope="col">At</th></tr></thead>
          <tbody>
            {r.timeline.map((t) => (
              <tr key={t.seq}><td className="n">{t.seq}</td><td>{ACTOR[t.actor] ?? t.actor}</td><td>{t.type}</td><td>{new Date(t.at).toLocaleTimeString("en-US")}</td></tr>
            ))}
          </tbody>
        </table>
      </>}
    </main>
  );
}
