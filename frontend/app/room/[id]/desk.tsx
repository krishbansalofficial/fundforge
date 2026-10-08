"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { api, money, pct, type View } from "../../lib";

const DAYS = [12, 13, 14, 15, 16, 17, 18, 19, 20, 21];
const PHASES = ["OPEN_ADMIN", "PUBLIC_MARK", "EXEC_A", "EXEC_B", "CLOSE"];
const PHASE_LABEL: Record<string, string> = {
  OPEN_ADMIN: "Opening admin", PUBLIC_MARK: "Market open", EXEC_A: "10:00 execution", EXEC_B: "15:00 execution", CLOSE: "Close",
};
const SIDES = ["SELL", "COVER", "BUY", "SHORT"];

function useSeatToken(roomId: string) {
  const [token, setToken] = useState<string | null>(null);
  useEffect(() => {
    const key = `ff-seat-${roomId}`;
    const fromUrl = new URLSearchParams(window.location.search).get("t");
    try {
      if (fromUrl) {
        sessionStorage.setItem(key, fromUrl);
        window.history.replaceState(null, "", window.location.pathname); // keep the seat token out of the address bar
      }
      setToken(fromUrl ?? sessionStorage.getItem(key));
    } catch {
      setToken(fromUrl);
    }
  }, [roomId]);
  return token;
}

export default function Desk({ roomId }: { roomId: string }) {
  const token = useSeatToken(roomId);
  const [v, setV] = useState<View | null>(null);
  const [error, setError] = useState("");
  const [flash, setFlash] = useState("");
  const [tab, setTab] = useState<"orders" | "investors" | "ledger" | "debrief">("orders");

  const refresh = useCallback(async () => {
    if (!token) return;
    try {
      setV(await api(`/api/rooms/${roomId}/view`, token));
      setError("");
    } catch (e) {
      setError((e as Error).message);
    }
  }, [roomId, token]);

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 1500); // polling is enough for two players; no socket until it isn't
    return () => clearInterval(t);
  }, [refresh]);

  useEffect(() => {
    if (v?.outcome) setTab("debrief");
  }, [v?.outcome]);

  const send = useCallback(
    async (cmd: Record<string, unknown>, done?: string) => {
      if (!token) return;
      try {
        await api(`/api/rooms/${roomId}/commands`, token, cmd);
        setFlash(done ?? "");
        await refresh();
      } catch (e) {
        setFlash(`Not done: ${(e as Error).message}`);
      }
    },
    [roomId, token, refresh],
  );

  if (token === null && !v) {
    return <main className="desk-empty"><p>Open this desk from your seat link. Ask your partner to resend it if it&rsquo;s lost.</p></main>;
  }
  if (!v) return <main className="desk-empty"><p>{error ? `Couldn't load the desk: ${error}` : "Loading the desk…"}</p></main>;

  const me = v.role as "pm" | "mp";
  const partner = me === "pm" ? "mp" : "pm";
  const f = v.fund;
  const headroom = Number(f.nav) - Number(f.maintenance_req);

  return (
    <main className="desk">
      <Ribbon v={v} />
      <section className="status" aria-label="Fund status">
        <Figure label="Net asset value" value={money(f.nav)} />
        <Figure label="Gross / net exposure" value={`${pct(f.gross)} / ${pct(f.net)}`} />
        <Headroom nav={Number(f.nav)} req={Number(f.maintenance_req)} />
        <Figure label="Cash / broker debt" value={`${money(f.cash)} / ${money(f.debt)}`} />
        <Figure label="Credit left" value={money(f.credit_left)} />
        <Figure label="Firm cash (not fund money)" value={money(v.firm.cash)} tone="firm" />
      </section>

      {f.margin_call && (
        <p className="alert" role="alert">
          Margin call of {money(f.margin_call, 2)}. Cure it at the next execution by selling longs or covering shorts, or the broker liquidates.
        </p>
      )}
      {v.recall.open > 0 && (
        <p className="alert soft" role="status">
          {v.recall.open.toLocaleString()} BRIN recalled. Cover by day 15 15:00
          {v.recall.offer_visible ? ", or accept the replacement borrow before day 14 15:00." : "."} Otherwise a forced buy-in executes.
        </p>
      )}

      <div className="grid">
        <Positions v={v} />
        <Feed v={v} />
        <Actions v={v} me={me} send={send} />
        <Partners v={v} me={me} partner={partner} send={send} flash={flash} />
      </div>

      <nav className="tabs" aria-label="Records">
        {(["orders", "investors", "ledger", "debrief"] as const).map((t) => (
          <button key={t} className={tab === t ? "on" : ""} aria-pressed={tab === t} onClick={() => setTab(t)}>
            {{ orders: "Orders and packages", investors: "Investors", ledger: "Ledger", debrief: "Debrief" }[t]}
          </button>
        ))}
      </nav>
      {tab === "orders" && <Orders v={v} me={me} send={send} />}
      {tab === "investors" && <Investors v={v} />}
      {tab === "ledger" && token && <Ledger roomId={roomId} token={token} version={v.version} />}
      {tab === "debrief" && <Debrief v={v} headroom={headroom} />}
    </main>
  );
}

function Figure({ label, value, tone }: { label: string; value: string; tone?: string }) {
  return (
    <div className={`figure ${tone ?? ""}`}>
      <span className="figure-label">{label}</span>
      <span className="figure-value">{value}</span>
    </div>
  );
}

function Headroom({ nav, req }: { nav: number; req: number }) {
  const ratio = req > 0 ? Math.min(nav / req, 1.6) : 1.6;
  const state = nav < req ? "breach" : ratio < 1.05 ? "tight" : "ok";
  return (
    <div className={`figure headroom ${state}`}>
      <span className="figure-label">Maintenance headroom</span>
      <span className="figure-value">{money(String(nav - req))}</span>
      <span className="bar" aria-hidden><span style={{ width: `${(ratio / 1.6) * 100}%` }} /><i /></span>
    </div>
  );
}

function Ribbon({ v }: { v: View }) {
  const cur = v.clock;
  const nxt = cur.next;
  const known = (text: string) => v.notices.some((n: any) => n.text.includes(text));
  const marks: Record<number, string> = {};
  if (known("redemption")) { marks[20] = "Tactical dealing"; marks[21] = "Redemption payment"; }
  if (known("stressed margin")) marks[16] = "Stressed margin";
  if (known("recalls")) marks[15] = "Recall deadline";
  if (known("BEAM may be suspended")) marks[20] = "Dealing; BEAM halt risk";
  const pos = (d: number, p: string) => (d - 12) * 5 + PHASES.indexOf(p);
  const here = nxt ? pos(nxt.day, nxt.phase) : 999;
  return (
    <header className="ribbon">
      <div className="ribbon-title">
        <span className="wordmark">FundForge</span>
        <span>
          {v.clock.finished ? "Season complete" : `Day ${cur.day}, ${new Date(cur.date + "T12:00:00").toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" })}`}
          {nxt && <> &ndash; next: {PHASE_LABEL[nxt.phase]}</>}
        </span>
      </div>
      <ol className="days">
        {DAYS.map((d) => (
          <li key={d} className={nxt && d === nxt.day ? "today" : ""}>
            <span className="day-n">Day {d}</span>
            <span className="ticks" aria-hidden>
              {(d === 21 ? PHASES.slice(0, 1) : PHASES).map((p) => (
                <i key={p} className={pos(d, p) < here ? "done" : pos(d, p) === here ? "now" : ""} />
              ))}
            </span>
            {marks[d] && <span className="deadline">{marks[d]}</span>}
          </li>
        ))}
      </ol>
    </header>
  );
}

function Positions({ v }: { v: View }) {
  const rows = v.positions.filter((p: any) => p.qty !== 0 || p.borrowed);
  return (
    <section className="panel positions" aria-labelledby="pos-h">
      <h2 id="pos-h">Book</h2>
      <table>
        <thead><tr><th>Name</th><th className="n">Shares</th><th className="n">Mark</th><th className="n">Value</th><th className="n">Borrowed</th></tr></thead>
        <tbody>
          {rows.map((p: any) => (
            <tr key={p.sym} className={p.qty < 0 ? "short" : ""}>
              <td>{p.sym}</td>
              <td className="n">{p.qty.toLocaleString()}</td>
              <td className="n">{Number(p.mark).toFixed(2)}</td>
              <td className="n">{money(p.mv)}</td>
              <td className="n">{p.borrowed ? p.borrowed.toLocaleString() : ""}</td>
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr><td colSpan={3}>Longs / shorts</td><td className="n" colSpan={2}>{money(v.fund.long_mv)} / {money(v.fund.short_mv)}</td></tr>
          <tr><td colSpan={3}>Restricted short collateral</td><td className="n" colSpan={2}>{money(v.fund.collateral)}</td></tr>
        </tfoot>
      </table>
    </section>
  );
}

function Feed({ v }: { v: View }) {
  const items = [...v.notices].reverse();
  return (
    <section className="panel feed" aria-labelledby="feed-h" aria-live="polite">
      <h2 id="feed-h">Desk feed</h2>
      {items.length === 0 ? <p className="muted">Nothing published yet.</p> : (
        <ul>
          {items.map((n: any, i: number) => (
            <li key={i} className={n.kind}>
              <span className="when">Day {n.day}</span>
              <span>{n.text}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

type Send = (cmd: Record<string, unknown>, done?: string) => Promise<void>;

function Actions({ v, me, send }: { v: View; me: string; send: Send }) {
  const [sym, setSym] = useState("BEAM");
  const [side, setSide] = useState("SELL");
  const [qty, setQty] = useState("");
  const [limit, setLimit] = useState("");
  const [reserve, setReserve] = useState("");
  const [topic, setTopic] = useState("");
  const atBarrier = v.clock.next && v.clock.next.phase.startsWith("EXEC");
  const order = () => ({ order_id: `${me}-${crypto.randomUUID().slice(0, 8)}`, sym, side, qty: Number(qty), ...(limit ? { limit } : {}) });
  const notional = Number(qty || 0) * Number(v.marks[sym] ?? 0);
  const ticketCap = Number(v.fund.nav) * 0.05;

  return (
    <section className="panel actions" aria-labelledby="act-h">
      <h2 id="act-h">{me === "pm" ? "Trade" : "Liquidity and borrow"}</h2>
      {!atBarrier && <p className="muted">Orders open at the next decision point.</p>}
      <form className="ticket" onSubmit={(e) => { e.preventDefault(); }}>
        <label>Side<select value={side} onChange={(e) => setSide(e.target.value)}>{SIDES.map((s) => <option key={s}>{s}</option>)}</select></label>
        <label>Name<select value={sym} onChange={(e) => setSym(e.target.value)}>{Object.keys(v.marks).map((s) => <option key={s}>{s}</option>)}</select></label>
        <label>Shares<input inputMode="numeric" value={qty} onChange={(e) => setQty(e.target.value.replace(/\D/g, ""))} placeholder="0" /></label>
        <label>Limit (optional)<input inputMode="decimal" value={limit} onChange={(e) => setLimit(e.target.value.replace(/[^\d.]/g, ""))} placeholder="Market" /></label>
        <p className="hint">≈ {money(String(notional))} at the current mark. Fills at the next execution, with impact.</p>
        <div className="row">
          {me === "pm" && (
            <button type="button" disabled={!atBarrier || !qty || notional > ticketCap}
              title={notional > ticketCap ? "Above 5% of NAV: propose it as a package" : ""}
              onClick={() => send({ type: "ticket", ...order() }, "Ticket queued for the next execution.").then(() => setQty(""))}>
              Send ticket
            </button>
          )}
          <button type="button" className="secondary" disabled={!atBarrier || !qty}
            onClick={() => send({ type: "propose", package_id: `pkg-${crypto.randomUUID().slice(0, 8)}`, orders: [order()] }, "Package sent for your partner's signature.").then(() => setQty(""))}>
            Propose to partner
          </button>
        </div>
      </form>

      {me === "mp" && (
        <div className="mp-tools">
          <div className="row">
            <select aria-label="Research topic" value={topic} onChange={(e) => setTopic(e.target.value)}>
              <option value="">Assign research ({v.research.budget - v.research.used.length} left)</option>
              {v.research.topics.filter((t: string) => !v.research.used.some((u: any) => u.topic === t)).map((t: string) => (
                <option key={t} value={t}>{{ borrow: "BRIN borrow availability", debt_schedule: "BRIN debt schedule", demand_survey: "BRIN demand survey" }[t] ?? t}</option>
              ))}
            </select>
            <button type="button" disabled={!topic || !atBarrier} onClick={() => send({ type: "research", topic }, "Research assigned; results arrive at the next market open.").then(() => setTopic(""))}>Assign</button>
          </div>
          {v.recall.offer_visible && !v.recall.replacement_accepted && (
            <button type="button" disabled={!atBarrier} onClick={() => send({ type: "accept_replacement" }, "Replacement borrow accepted. It transfers day 15 at 40%.")}>
              Accept replacement borrow (1,250 BRIN at 40%)
            </button>
          )}
          <div className="row">
            <input inputMode="decimal" aria-label="Treasury reserve in dollars" placeholder={`Reserve, now ${money(v.fund.reserve)}`} value={reserve}
              onChange={(e) => setReserve(e.target.value.replace(/[^\d.]/g, ""))} />
            <button type="button" disabled={!reserve} onClick={() => send({ type: "set_reserve", amount: reserve }, "Treasury reserve set.").then(() => setReserve(""))}>Set reserve</button>
          </div>
        </div>
      )}
    </section>
  );
}

function Partners({ v, me, partner, send, flash }: { v: View; me: string; partner: string; send: Send; flash: string }) {
  const ready = v.ready.includes(me);
  const waiting = v.packages.filter((p: any) => p.status === "PENDING_APPROVAL" && p.proposer === partner);
  return (
    <section className="panel partners" aria-labelledby="ptn-h">
      <h2 id="ptn-h">Committee</h2>
      <p>
        You are <strong>{v.names[me]}</strong>, {me === "pm" ? "portfolio manager" : "managing partner"}. {v.names[partner]} is{" "}
        {v.ready.includes(partner) ? "ready to move on" : "still deciding"}.
      </p>
      {waiting.map((p: any) => (
        <div key={p.package_id} className="to-sign">
          <p>{v.names[partner]} asks you to approve:</p>
          <ul>{p.orders.map((o: any) => <li key={o.order_id}>{o.side} {Number(o.qty).toLocaleString()} {o.sym}{o.limit ? ` limit ${o.limit}` : ""}</li>)}</ul>
          <p className="digest" title="Your signature binds to this exact content hash">Contents hash {p.digest.slice(0, 12)}</p>
          <button type="button" onClick={() => send({ type: "sign", package_id: p.package_id, digest: p.digest }, "Signed. The package executes at the next execution.")}>Sign package</button>
        </div>
      ))}
      {!v.clock.finished && (
        <button type="button" className="ready" disabled={ready} onClick={() => send({ type: "ready" }, "")}>
          {ready ? `Waiting for ${v.names[partner]}` : `Ready: advance to ${v.clock.next ? PHASE_LABEL[v.clock.next.phase].toLowerCase() : "the end"}`}
        </button>
      )}
      {flash && <p className="flash" role="status">{flash}</p>}
    </section>
  );
}

function Orders({ v, me, send }: { v: View; me: string; send: Send }) {
  return (
    <section className="panel wide">
      <table>
        <thead><tr><th>Order</th><th>Instruction</th><th className="n">Filled</th><th>Status</th><th>Fills</th><th /></tr></thead>
        <tbody>
          {v.orders.length === 0 && <tr><td colSpan={6} className="muted">No orders yet. Tickets and signed packages appear here.</td></tr>}
          {[...v.orders].reverse().map((o: any) => (
            <tr key={o.order_id} className={o.forced ? "forced" : ""}>
              <td>{o.forced ? `Broker forced (${o.forced})` : o.order_id}</td>
              <td>{o.side} {o.qty.toLocaleString()} {o.sym}</td>
              <td className="n">{o.filled.toLocaleString()}</td>
              <td>{o.status.replaceAll("_", " ").toLowerCase()}</td>
              <td>{o.fills.map((x: any, i: number) => <div key={i}>{x.rejected ? `Rejected: ${x.rejected}` : `Day ${x.day} ${x.qty.toLocaleString()} @ ${x.price}`}</div>)}</td>
              <td>{["QUEUED", "PARTIALLY_FILLED"].includes(o.status) && !o.forced && <button type="button" className="link" onClick={() => send({ type: "cancel", order_id: o.order_id }, "Order canceled.")}>Cancel</button>}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {v.packages.length > 0 && (
        <table>
          <thead><tr><th>Package</th><th>Proposed by</th><th>Contents</th><th>Signatures</th><th>Status</th></tr></thead>
          <tbody>
            {v.packages.map((p: any) => (
              <tr key={p.package_id}>
                <td>{p.digest.slice(0, 10)}</td>
                <td>{v.names[p.proposer]}{p.proposer === me ? " (you)" : ""}</td>
                <td>{p.orders.map((o: any) => `${o.side} ${o.qty} ${o.sym}`).join(", ")}</td>
                <td>{p.signatures.map((s: string) => v.names[s]).join(" and ")}</td>
                <td>{p.status.replaceAll("_", " ").toLowerCase()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}

function Investors({ v }: { v: View }) {
  return (
    <section className="panel wide">
      <table>
        <thead><tr><th>Series</th><th className="n">Units</th><th className="n">Net capital</th><th className="n">NAV per unit</th><th className="n">High-water mark</th><th className="n">Performance provision</th></tr></thead>
        <tbody>
          {v.series.map((s: any) => (
            <tr key={s.id}><td>{s.id}</td><td className="n">{Number(s.units).toLocaleString()}</td><td className="n">{money(s.net, 2)}</td>
              <td className="n">{Number(s.nav_per_unit).toFixed(4)}</td><td className="n">{Number(s.hwm).toFixed(2)}</td><td className="n">{money(s.provision, 2)}</td></tr>
          ))}
        </tbody>
      </table>
      <p className="muted">The management company is a separate entity: {money(v.firm.cash)} cash, {money(v.firm.fee_receivable, 2)} fees receivable, {money(v.firm.payroll_payable)} payroll owed. Fees receivable are not spendable until the fund pays them.</p>
    </section>
  );
}

function Ledger({ roomId, token, version }: { roomId: string; token: string; version: number }) {
  const [entity, setEntity] = useState<"fund" | "firm">("fund");
  const [data, setData] = useState<any>(null);
  useEffect(() => {
    api(`/api/rooms/${roomId}/ledger?entity=${entity}`, token).then(setData).catch(() => setData(null));
  }, [roomId, token, entity, version]);
  const entries = useMemo(() => (data ? [...data.entries].reverse() : []), [data]);
  return (
    <section className="panel wide ledger">
      <div className="row">
        <button type="button" className={entity === "fund" ? "on" : "secondary"} onClick={() => setEntity("fund")}>Fund journal</button>
        <button type="button" className={entity === "firm" ? "on" : "secondary"} onClick={() => setEntity("firm")}>Management company journal</button>
        {data && <span className="digest" title="SHA-256 over every entry; identical inputs replay to the same hash">Journal hash {data.digest.slice(0, 16)}</span>}
      </div>
      <table>
        <thead><tr><th>Date</th><th>Entry</th><th>Account</th><th className="n">Debit</th><th className="n">Credit</th></tr></thead>
        <tbody>
          {entries.slice(0, 150).flatMap((e: any) =>
            e.postings.map(([acct, amt]: [string, string], i: number) => (
              <tr key={e.id + i} className={i === 0 ? "entry-start" : ""}>
                <td>{i === 0 ? e.date : ""}</td><td>{i === 0 ? e.memo : ""}</td><td>{acct}</td>
                <td className="n">{Number(amt) > 0 ? money(amt, 2) : ""}</td><td className="n">{Number(amt) < 0 ? money(String(-Number(amt)), 2) : ""}</td>
              </tr>
            )),
          )}
        </tbody>
      </table>
    </section>
  );
}

function Debrief({ v, headroom }: { v: View; headroom: number }) {
  const o = v.outcome;
  if (!o) {
    return (
      <section className="panel wide">
        <p className="muted">The debrief opens after the day 21 payment. So far: {v.incidents.length ? v.incidents.join("; ") : "no forced actions or unpaid claims"}. Maintenance headroom is {money(String(headroom))}.</p>
      </section>
    );
  }
  const verdict: Record<string, string> = {
    WIN: "You kept control. The recall was resolved without a forced buy-in, nothing was liquidated, and Tactical was paid on time.",
    SURVIVAL: "The fund survived and paid its investors, but the broker acted for you. The forced trades are listed below.",
    DISTRESS: "Claims went unpaid or NAV failed. Each shortfall is listed below and stays on the books.",
  };
  return (
    <section className="panel wide debrief">
      <h2 className={`verdict ${o.label.toLowerCase()}`}>{o.label === "WIN" ? "Win" : o.label === "SURVIVAL" ? "Survival" : "Distress"}</h2>
      <p>{verdict[o.label]}</p>
      <dl>
        <dt>Ending NAV</dt><dd>{money(o.nav, 2)}</dd>
        <dt>Tactical redemption paid</dt><dd>{money(o.redemption_paid, 2)}</dd>
        <dt>Recall resolved by</dt><dd>{o.recall_resolved_by ?? "unresolved"}</dd>
        <dt>Forced actions</dt><dd>{o.forced.length ? o.forced.join("; ") : "none"}</dd>
        <dt>Unpaid or failed</dt><dd>{o.unpaid.length ? o.unpaid.join("; ") : "none"}</dd>
        <dt>Replay proof</dt><dd className="digest">tape {o.tape_digest.slice(0, 12)}, journal {o.journal_digest.slice(0, 12)}</dd>
      </dl>
    </section>
  );
}
