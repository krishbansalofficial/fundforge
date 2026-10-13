"use client";

import { useEffect, useState } from "react";
import { api, complement, money, num, type Command, type Forecast, type TerminalView } from "../../lib";

// GET /api/rooms/{id}/terminal, generated from the server contract (fundforge.schemas.TerminalView).
// Values are Decimal strings, formatted only.
type Snapshot = TerminalView;
type Sample = Snapshot["history"][number];
type Regime = NonNullable<Snapshot["regime"]>;
/** A thesis this seat sent (from the view's decision log). */
export type Thesis = { question: string; forecast: Forecast };

const bps = (s: string | null) => (s == null ? "—" : `${Number(s) > 0 ? "+" : ""}${Number(s).toFixed(1)}`);

/** Research view. Refetches when the room version changes; its only command is the regime thesis,
 *  sent through the desk's single-flight `send`. */
export function Terminal({ roomId, token, version, theses, send, busy }: {
  roomId: string; token: string; version: number; theses: Thesis[]; send: Send; busy: boolean;
}) {
  const [t, setT] = useState<Snapshot | null>(null);
  const [error, setError] = useState("");
  const [sym, setSym] = useState("");
  useEffect(() => {
    let cancelled = false;
    api(`/api/rooms/${roomId}/terminal`, token)
      .then((got: Snapshot) => {
        if (cancelled) return;
        setT((old) => (old && old.version > got.version ? old : got)); // a late response never replaces newer data
        setError("");
      })
      .catch((e: unknown) => { if (!cancelled) setError(e instanceof Error ? e.message : "Terminal unavailable"); });
    return () => { cancelled = true; };
  }, [roomId, token, version]);

  if (!t) return <section className="panel wide"><p role={error ? "alert" : "status"}>{error ? `Terminal unavailable: ${error}` : "Loading the terminal…"}</p></section>;
  const selected = t.quotes.some((q) => q.sym === sym) ? sym : (t.quotes[0]?.sym ?? "");
  const r = t.risk;
  const macro = [...(t.macro ?? [])].sort((a, b) => b.period_day - a.period_day || b.revision - a.revision);
  return (
    <section className="panel wide terminal" aria-labelledby="term-h">
      <h2 id="term-h">Forge Terminal</h2>
      <p className="muted">As of day {t.as_of.day} ({t.as_of.date}), processed event {t.as_of.event}. Synthetic processed-event marks; read only.</p>
      {error && <p role="alert">{error}. Showing the last loaded snapshot.</p>}
      <div className="grid">
        <div>
          <table aria-label="Market monitor">
            <thead><tr><th scope="col">Name</th><th scope="col" className="n">Mark</th><th scope="col" className="n">Last event bps</th>
              <th scope="col" className="n">Since start bps</th><th scope="col" className="n">Position</th><th scope="col" className="n">Borrow APR</th></tr></thead>
            <tbody>
              {t.quotes.map((q) => (
                <tr key={q.sym}>
                  <th scope="row"><button type="button" className={q.sym === selected ? "link on" : "link"} aria-pressed={q.sym === selected}
                    aria-label={`Chart ${q.sym}`} onClick={() => setSym(q.sym)}>{q.sym}</button></th>
                  <td className="n">{Number(q.mark).toFixed(2)}</td>
                  <td className="n">{bps(q.change_bps)}</td>
                  <td className="n">{bps(q.since_start_bps)}</td>
                  <td className="n">{num(q.qty)}</td>
                  <td className="n">{q.borrow_rate == null ? "" : `${(Number(q.borrow_rate) * 100).toFixed(1)}%`}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div>
          <Chart sym={selected} history={t.history} truncated={t.history_truncated} />
          <dl className="fund-watch" aria-label="Fund watch">
            <dt>NAV</dt><dd>{money(r.nav)}</dd>
            <dt>Maintenance headroom</dt><dd>{money(r.headroom)}</dd>
            <dt>Cash</dt><dd>{money(r.cash)}</dd>
            <dt>Restricted short collateral</dt><dd>{money(r.restricted_collateral)}</dd>
          </dl>
        </div>
      </div>
      <table aria-label="Static stress">
        <caption className="muted">{r.stress_method}</caption>
        <thead><tr><th scope="col">Scenario</th><th scope="col" className="n">Mark P&amp;L</th><th scope="col" className="n">NAV</th><th scope="col" className="n">Headroom</th><th scope="col">Margin</th></tr></thead>
        <tbody>
          {r.stresses.map((s) => (
            <tr key={s.id}><th scope="row">{s.label}</th><td className="n">{money(s.pnl)}</td><td className="n">{money(s.nav)}</td>
              <td className="n">{money(s.headroom)}</td><td>{s.margin_breach ? "Breach" : "OK"}</td></tr>
          ))}
        </tbody>
      </table>
      {t.regime && <RegimeResearch r={t.regime} mine={theses.filter((x) => x.question === t.regime!.question).at(-1)} send={send} busy={busy} />}
      {macro.length > 0 && (
        <table aria-label="STREET_ACTIVITY index, newest first">
          <caption>STREET_ACTIVITY index (published prints only)</caption>
          <thead><tr><th scope="col">Period day</th><th scope="col" className="n">Value</th><th scope="col">Print</th><th scope="col">Published day</th></tr></thead>
          <tbody>
            {macro.map((m) => (
              <tr key={`${m.series}:${m.period_day}:${m.revision}`}><th scope="row">Day {m.period_day}</th><td className="n">{m.value}</td>
                <td>{m.revision === 0 ? "first print" : "revised"}</td><td>Day {m.published_day}</td></tr>
            ))}
          </tbody>
        </table>
      )}
      <h3>Latest headlines</h3>
      {t.news.length === 0 ? <p className="muted">Nothing published yet.</p> : (
        <ul aria-label="Latest headlines, newest first">
          {t.news.slice(-8).reverse().map((n, i) => <li key={i}><span className="when">Day {n.day}</span> {n.text}</li>)}
        </ul>
      )}
    </section>
  );
}

/** Observed marks, one point per processed event (evenly spaced); no candles or invented intraday path. */
function Chart({ sym, history, truncated }: { sym: string; history: Sample[]; truncated: boolean }) {
  const pts = history.filter((h) => h.marks[sym] != null).map((h) => ({ day: h.day, y: Number(h.marks[sym]) }));
  if (pts.length === 0) return <p className="muted">No observed history for {sym || "this name"} yet.</p>;
  const lo = Math.min(...pts.map((p) => p.y)), hi = Math.max(...pts.map((p) => p.y));
  const W = 600, H = 180, pad = 8;
  const x = (i: number) => (pts.length === 1 ? W / 2 : pad + (i * (W - 2 * pad)) / (pts.length - 1));
  const y = (v: number) => (hi === lo ? H / 2 : pad + ((hi - v) * (H - 2 * pad)) / (hi - lo));
  const first = pts[0], last = pts[pts.length - 1];
  const summary = `${sym} observed marks over ${pts.length} processed events${truncated ? " (most recent only)" : ""}: `
    + `${first.y.toFixed(2)} on day ${first.day} to ${last.y.toFixed(2)} on day ${last.day}; low ${lo.toFixed(2)}, high ${hi.toFixed(2)}.`;
  return (
    <figure className="chart">
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label={summary}>
        <polyline fill="none" stroke="currentColor" strokeWidth="2" points={pts.map((p, i) => `${x(i).toFixed(1)},${y(p.y).toFixed(1)}`).join(" ")} />
      </svg>
      <figcaption className="muted">{summary}</figcaption>
    </figure>
  );
}

export type Send = (cmd: Command, done?: string) => Promise<void>;

/** The live regime question: published prior and exact posterior, plus this seat's thesis ticket. */
function RegimeResearch({ r, mine, send, busy }: { r: Regime; mine?: Thesis; send: Send; busy: boolean }) {
  const [calm, setCalm] = useState("");
  const stressed = complement(calm);
  const invalid = calm.trim() !== "" && stressed == null;
  return (
    <section className="regime" aria-labelledby="regime-h">
      <h3 id="regime-h">Regime research: is day {r.period_day} calm or stressed?</h3>
      <table aria-label="Regime probabilities">
        <caption className="muted">
          Posterior from the {r.evidence} published STREET_ACTIVITY prints, not a forecast of prices. {r.method}
        </caption>
        <thead><tr><th scope="col">Regime</th><th scope="col" className="n">Published prior</th><th scope="col" className="n">Posterior from published prints</th></tr></thead>
        <tbody>
          <tr><th scope="row">Calm</th><td className="n">{r.prior.calm}</td><td className="n">{r.posterior.calm}</td></tr>
          <tr><th scope="row">Stressed</th><td className="n">{r.prior.stressed}</td><td className="n">{r.posterior.stressed}</td></tr>
        </tbody>
      </table>
      <p role="status">{mine ? `Your thesis for ${r.question}: calm ${mine.forecast.calm}, stressed ${mine.forecast.stressed}. Scored in the debrief, never in P&L.`
        : `You have no thesis for ${r.question} yet.`}</p>
      <form className="row" onSubmit={(e) => {
        e.preventDefault();
        if (stressed == null) return;
        send({ type: "thesis", question: r.question, forecast: { calm: calm.trim(), stressed } }, `Thesis recorded for ${r.question}.`)
          .then(() => setCalm(""));
      }}>
        <fieldset className="contents" disabled={busy} aria-busy={busy}>
          <label>Your calm probability
            <input inputMode="decimal" value={calm} onChange={(e) => setCalm(e.target.value)} placeholder="0 to 1, e.g. 0.35"
              aria-invalid={invalid} aria-describedby="thesis-hint" />
          </label>
          <p id="thesis-hint" className={invalid ? "hint error" : "hint"}>
            {invalid ? "Enter a number from 0 to 1 with at most 6 decimals." : `Stressed: ${stressed ?? "—"} (1 − calm, exact).`}
          </p>
          <button type="submit" disabled={stressed == null}>Submit thesis</button>
        </fieldset>
      </form>
    </section>
  );
}
