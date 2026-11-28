"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { call, type LeaderRow } from "../account";
import { SCENARIOS } from "../lib";
import { Nav } from "../nav";

/** Verified results only: every row is a finished room the server replayed from its command log. */
export default function Leaderboard() {
  const [scenario, setScenario] = useState("case1");
  const [rows, setRows] = useState<LeaderRow[] | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    setRows(null);
    call<LeaderRow[]>(`/api/leaderboard?scenario=${encodeURIComponent(scenario)}`)
      .then((r) => { setRows(r); setError(""); })
      .catch((e: Error) => setError(e.message));
  }, [scenario]);

  return (
    <main className="landing">
      <Nav />
      <h1>Leaderboard</h1>
      <p className="lede">
        Score is excess return over a passive copy of the opening book, in basis points, minus a penalty per forced action.
        The server replayed and verified every row from its command log before ranking it.
      </p>
      <label className="tw:grid tw:max-w-md tw:gap-1">
        Scenario
        <select value={scenario} onChange={(e) => setScenario(e.target.value)}>
          {SCENARIOS.map(([key, text]) => <option key={key} value={key}>{text}</option>)}
        </select>
      </label>
      {error && <p className="error" role="alert">{error}</p>}
      {rows === null ? <p role="status">Loading…</p> : rows.length === 0 ? <p>No verified results yet. <Link href="/">Be the first.</Link></p> : (
        <table>
          <thead><tr><th scope="col" className="n">Rank</th><th scope="col">Partners</th><th scope="col">Result</th><th scope="col" className="n">Score</th><th scope="col">Replay</th></tr></thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.room_id}>
                <td className="n">{r.rank}</td>
                <td>{r.players.pm} &amp; {r.players.mp}</td>
                <td>{r.label}</td>
                <td className="n">{Number(r.score).toFixed(2)}</td>
                <td><Link href={`/replay/${r.room_id}`}>Replay {r.room_id}</Link></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </main>
  );
}
