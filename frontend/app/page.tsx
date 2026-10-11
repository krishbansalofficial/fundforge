"use client";

import { useState } from "react";
import { api } from "./lib";

type Room = { room_id: string; tokens: { pm: string; mp: string }; names: { pm: string; mp: string } };

export default function Home() {
  const [pm, setPm] = useState("");
  const [mp, setMp] = useState("");
  const [room, setRoom] = useState<Room | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function create(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      setRoom(await api("/api/rooms", undefined, { scenario: "case1", pm_name: pm || "Ana", mp_name: mp || "Ben" }));
    } catch (err) {
      setError(`Couldn't open the fund: ${(err as Error).message}. Check that the API is running.`);
    } finally {
      setBusy(false);
    }
  }

  const link = (role: "pm" | "mp") =>
    room ? `${typeof window === "undefined" ? "" : window.location.origin}/room/${room.room_id}#t=${room.tokens[role]}` : "";

  return (
    <main className="landing">
      <header className="landing-head">
        <p className="wordmark">FundForge</p>
        <h1>Ten trading days. One recalled borrow. Twenty-five million dollars that isn&rsquo;t yours.</h1>
        <p className="lede">
          You and a partner run a fictional long/short fund in the middle of a crisis. The prime broker wants 1,250 BRIN
          shares back, a market shock is coming, and the Tactical investors expect their money on day 21. The management
          company has payroll of its own, and investor cash can&rsquo;t cover it.
        </p>
      </header>

      <section className="roles">
        <div>
          <h2>Portfolio manager</h2>
          <p>Owns exposure. Sends tickets up to 5% of NAV alone. Larger moves need the partner&rsquo;s signature on the exact package.</p>
        </div>
        <div>
          <h2>Managing partner</h2>
          <p>Owns liquidity. Chooses research, accepts replacement borrow, sets the treasury reserve, and countersigns packages.</p>
        </div>
      </section>

      {!room ? (
        <form className="open-form" onSubmit={create}>
          <label>
            Portfolio manager&rsquo;s name
            <input value={pm} onChange={(e) => setPm(e.target.value)} maxLength={40} placeholder="Ana" />
          </label>
          <label>
            Managing partner&rsquo;s name
            <input value={mp} onChange={(e) => setMp(e.target.value)} maxLength={40} placeholder="Ben" />
          </label>
          <button type="submit" disabled={busy}>{busy ? "Opening…" : "Open the fund"}</button>
          {error && <p className="error" role="alert">{error}</p>}
        </form>
      ) : (
        <section className="seats" aria-live="polite">
          <p>The fund is open. Each partner gets a private seat link. Send the other link to your partner.</p>
          {(["pm", "mp"] as const).map((r) => (
            <div key={r} className="seat">
              <span>{room.names[r]}, {r === "pm" ? "portfolio manager" : "managing partner"}</span>
              <input readOnly value={link(r)} onFocus={(e) => e.currentTarget.select()} aria-label={`Seat link for ${room.names[r]}`} />
              <a href={link(r)}>Take this seat</a>
            </div>
          ))}
        </section>
      )}

      <footer className="fineprint">
        Fictional money and entities. No brokerage, no real capital, no investment advice. The accounting is deterministic and replayable.
      </footer>
    </main>
  );
}
