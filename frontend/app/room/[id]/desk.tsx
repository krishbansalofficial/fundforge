"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { exclusive } from "../../exclusive";
import { seatTokenFromUrl } from "../../seat";
import { api, exactPct, fetchView, money, num, pct, type Command, type Debrief as DebriefResponse, type Decision, type LedgerPage, type Side, type View } from "../../lib";
import { Terminal, type Send, type Thesis } from "./terminal";

const DAYS = [12, 13, 14, 15, 16, 17, 18, 19, 20, 21];
const PHASES = ["OPEN_ADMIN", "PUBLIC_MARK", "EXEC_A", "EXEC_B", "CLOSE"];
const PHASE_LABEL: Record<string, string> = {
  OPEN_ADMIN: "Opening admin", PUBLIC_MARK: "Market open", EXEC_A: "10:00 execution", EXEC_B: "15:00 execution", CLOSE: "Close",
};
const SIDES: Side[] = ["SELL", "COVER", "BUY", "SHORT"];

function useSeatToken(roomId: string) {
  const [token, setToken] = useState<string | null>(null);
  useEffect(() => {
    const key = `ff-seat-${roomId}`;
    const fromUrl = seatTokenFromUrl(window.location.hash, window.location.search);
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
  const [tab, setTab] = useState<"orders" | "terminal" | "investors" | "ledger" | "debrief">("orders");

  const etag = useRef("");
  const refresh = useCallback(async () => {
    if (!token) return;
    try {
      const got = await fetchView(`/api/rooms/${roomId}/view`, token, etag.current);
      if (got) {
        etag.current = got.etag;
        setV(got.view);
      }
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

  // One command in flight per desk: a double-click must not send a second order with a new id and key.
  const inFlight = useRef(false);
  const [busy, setBusy] = useState(false);
  // Keyboard focus survives a command: the fieldset disables the pressed control while the command is in
  // flight, and Sign/Accept/Ready may then disappear or stay disabled. Without this, focus falls to <body>
  // and a keyboard player starts again from the top of the page.
  const focusBefore = useRef<HTMLElement | null>(null);
  useEffect(() => {
    const prev = focusBefore.current;
    if (busy || !prev) return;
    focusBefore.current = null;
    const now = document.activeElement as HTMLElement | null;
    if (now && now !== document.body && now !== prev && now.isConnected) return; // the player moved on
    if (prev.isConnected && !prev.matches(":disabled")) { prev.focus(); return; }
    const heading = (prev.isConnected ? prev.closest("section") : null)?.querySelector<HTMLElement>("h2, h3")
      ?? document.getElementById("ptn-h");
    heading?.focus();
  }, [busy, v]);
  const send = useCallback(
    async (cmd: Command, done?: string) => {
      if (!token) return "No seat token.";
      const active = document.activeElement;
      if (active instanceof HTMLElement && active !== document.body) focusBefore.current = active;
      let refused = "Another command is still in flight." as string | null;
      await exclusive(inFlight, async () => {
        setBusy(true);
        try {
          await api(`/api/rooms/${roomId}/commands`, token, cmd);
          refused = null;
          setFlash(done ?? "");
          await refresh();
        } catch (e) {
          refused = (e as Error).message;
          setFlash(`Not done: ${refused}`);
        } finally {
          setBusy(false);
        }
      });
      return refused;
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
        <div className="figure">
          <span className="figure-label">Net asset value</span>
          <span className="figure-value">{money(f.nav)}</span>
          <span>Latest dealing-close: {v.certification === "certified" ? "Certified" : v.certification === "broken" ? "Broken" : "Pending"}</span>
          <small>{v.certification === "broken" ? "Latest dealing was withheld; inspect RISK certification. " : v.certification !== "certified" ? "No dealing-close certificate yet. " : ""}Status applies to the latest dealing close, not a new check of current NAV.</small>
        </div>
        <Figure label="Gross / net exposure" value={`${pct(f.gross)} / ${pct(f.net)}`} />
        <Headroom nav={Number(f.nav)} req={Number(f.maintenance_req)} />
        <Figure label="Cash / broker debt" value={`${money(f.cash)} / ${money(f.debt)}`} />
        <Figure label="Credit left" value={money(f.credit_left)} />
        <Figure label="Firm cash (not fund money)" value={money(v.firm.cash)} tone="firm" />
      </section>

      {error && <p className="alert soft" role="status">Connection problem: {error}. Showing the last loaded desk.</p>}
      {f.margin_call && (
        <p className="alert" role="alert">
          Margin call of {money(f.margin_call, 2)}. Cure it at the next execution by selling longs or covering shorts, or the broker liquidates.
        </p>
      )}
      {v.recall.open > 0 && (
        <p className="alert soft" role="status">
          {num(v.recall.open)} BRIN recalled. Cover by day 15 15:00
          {v.recall.offer_visible ? ", or accept the replacement borrow before day 14 15:00." : "."} Otherwise a forced buy-in executes.
        </p>
      )}

      <div className="grid">
        <Positions v={v} />
        <Feed v={v} />
        <fieldset className="contents" disabled={busy} aria-busy={busy}>
          <Actions v={v} me={me} send={send} />
          <Partners v={v} me={me} partner={partner} send={send} flash={flash} />
        </fieldset>
      </div>

      <nav className="tabs" aria-label="Records">
        {(["orders", "terminal", "investors", "ledger", "debrief"] as const).map((t) => (
          <button key={t} className={tab === t ? "on" : ""} aria-pressed={tab === t} onClick={() => setTab(t)}>
            {{ orders: "Orders and packages", terminal: "Terminal", investors: "Investors", ledger: "Ledger", debrief: "Debrief" }[t]}
          </button>
        ))}
      </nav>
      {tab === "orders" && <fieldset className="contents" disabled={busy}><Orders v={v} me={me} send={send} /></fieldset>}
      {tab === "terminal" && token && <Terminal roomId={roomId} token={token} version={v.version} send={send} busy={busy}
        theses={v.decisions.filter((d) => d.type === "thesis" && d.role === me).map((d) => d.detail as Thesis)} />}
      {tab === "investors" && <fieldset className="contents" disabled={busy}><Investors v={v} send={send} /></fieldset>}
      {tab === "ledger" && token && <Ledger roomId={roomId} token={token} version={v.version} />}
      {tab === "debrief" && <Debrief v={v} headroom={headroom} roomId={roomId} token={token} />}
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
  const known = (text: string) => v.notices.some((n) => n.text.includes(text));
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
      <ol className="days" tabIndex={0} aria-label="Season calendar">
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
  const rows = v.positions.filter((p) => p.qty !== 0 || p.borrowed);
  return (
    <section className="panel positions" aria-labelledby="pos-h">
      <h2 id="pos-h">Book</h2>
      <table>
        <thead><tr><th>Name</th><th className="n">Shares</th><th className="n">Mark</th><th className="n">Value</th><th className="n">Borrowed</th></tr></thead>
        <tbody>
          {rows.map((p) => (
            <tr key={p.sym} className={p.qty < 0 ? "short" : ""}>
              <td>{p.sym}</td>
              <td className="n">{num(p.qty)}</td>
              <td className="n">{Number(p.mark).toFixed(2)}</td>
              <td className="n">{money(p.mv)}</td>
              <td className="n">{p.borrowed ? num(p.borrowed) : ""}</td>
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
        <ul tabIndex={0} aria-label="Published notices, newest first">
          {items.map((n, i) => (
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


function Actions({ v, me, send }: { v: View; me: string; send: Send }) {
  const [sym, setSym] = useState("BEAM");
  const [side, setSide] = useState<Side>("SELL");
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
        <label>Side<select value={side} onChange={(e) => setSide(e.target.value as Side)}>{SIDES.map((s) => <option key={s}>{s}</option>)}</select></label>
        <label>Name<select value={sym} onChange={(e) => setSym(e.target.value)}>{Object.keys(v.marks).map((s) => <option key={s}>{s}</option>)}</select></label>
        <label>Shares<input inputMode="numeric" value={qty} onChange={(e) => setQty(e.target.value.replace(/\D/g, ""))} placeholder="0" /></label>
        <label>Limit (optional)<input inputMode="decimal" value={limit} onChange={(e) => setLimit(e.target.value.replace(/[^\d.]/g, ""))} placeholder="Market" /></label>
        <p className="hint">≈ {money(String(notional))} at the current mark. Fills at the next execution, with impact.</p>
        <div className="row">
          {me === "pm" && (
            <button type="button" disabled={!atBarrier || !qty || notional > ticketCap}
              title={notional > ticketCap ? "Above 5% of NAV: propose it as a package" : ""}
              onClick={() => send({ type: "ticket", ...order() }, "Ticket queued for the next execution.").then((no) => { if (!no) setQty(""); })}>
              Send ticket
            </button>
          )}
          <button type="button" className="secondary" disabled={!atBarrier || !qty}
            onClick={() => send({ type: "propose", package_id: `pkg-${crypto.randomUUID().slice(0, 8)}`, orders: [order()] }, "Package sent for your partner's signature.").then((no) => { if (!no) setQty(""); })}>
            Propose to partner
          </button>
        </div>
      </form>

      <div className="mp-tools">
          <p className="muted">One assignment per decision window. Evidence stays private until its owner shares it.</p>
          <div className="row">
            <select aria-label="Research topic" value={topic} onChange={(e) => setTopic(e.target.value)}>
              <option value="">Assign research ({v.research.budget - v.research.used.length} left)</option>
              {v.research.topics.filter((t) => !v.research.used.some((u) => u.topic === t)).map((t) => (
                <option key={t} value={t}>{{ borrow: "BRIN borrow availability", debt_schedule: "BRIN debt schedule", demand_survey: "BRIN demand survey" }[t] ?? t}</option>
              ))}
            </select>
            <button type="button" disabled={!topic || !atBarrier || v.attention?.committed}
              onClick={() => send({ type: "visit", location: v.research.assignments[topic].location, assignment: topic },
                "Attention committed; private evidence arrives at the next market open.").then(() => setTopic(""))}>Assign</button>
          </div>
          {v.attention?.committed ? <p>Your attention is committed for this window.</p> : null}
          {v.research.evidence.map((evidence) => {
            const topic = String(evidence.refs.topic ?? ""), owner = String(evidence.refs.owner ?? "");
            const shared = v.research.shared.includes(topic);
            return <article key={topic}>
              <h3>{shared ? "Shared" : "Private"}: {topic.replaceAll("_", " ")}</h3>
              <p>{evidence.text}</p>
              {owner === me && !shared ? <button type="button"
                onClick={() => send({ type: "share_research", topic: topic }, "Evidence shared with your partner.")}>
                Share evidence with partner
              </button> : null}
            </article>;
          })}
      </div>
      {me === "mp" && (
        <div className="mp-tools">
          {v.recall.offer_visible && !v.recall.replacement_accepted && (
            <button type="button" disabled={!atBarrier} onClick={() => send({ type: "accept_replacement" }, "Replacement borrow accepted. It transfers day 15 at 40%.")}>
              Accept replacement borrow (1,250 BRIN at 40%)
            </button>
          )}
          <div className="row">
            <input inputMode="decimal" aria-label="Treasury reserve in dollars" placeholder={`Reserve, now ${money(v.fund.reserve)}`} value={reserve}
              onChange={(e) => setReserve(e.target.value.replace(/[^\d.]/g, ""))} />
            <button type="button" disabled={!reserve} onClick={() => send({ type: "set_reserve", amount: reserve }, "Treasury reserve set.").then((no) => { if (!no) setReserve(""); })}>Set reserve</button>
          </div>
        </div>
      )}
    </section>
  );
}

function Partners({ v, me, partner, send, flash }: { v: View; me: string; partner: string; send: Send; flash: string }) {
  const ready = v.ready.includes(me);
  const waiting = v.packages.filter((p) => p.status === "PENDING_APPROVAL" && p.proposer === partner);
  return (
    <section className="panel partners" aria-labelledby="ptn-h">
      <h2 id="ptn-h">Committee</h2>
      <p>
        You are <strong>{v.names[me]}</strong>, {me === "pm" ? "portfolio manager" : "managing partner"}. {v.names[partner]} is{" "}
        {v.ready.includes(partner) ? "ready to move on" : "still deciding"}.
      </p>
      {waiting.map((p) => (
        <div key={p.package_id} className="to-sign">
          <p>{v.names[partner]} asks you to approve:</p>
          <ul>{p.orders.map((o) => <li key={o.order_id}>{o.side} {num(o.qty)} {o.sym}{o.limit ? ` limit ${o.limit}` : ""}</li>)}</ul>
          {p.kind === "gate" && <p>{gateText(p.terms)}</p>}
          <p className="digest" title="Your signature binds to this exact content hash">Contents hash {p.digest.slice(0, 12)}</p>
          <button type="button" onClick={() => send({ type: "sign", package_id: p.package_id, digest: p.digest }, p.kind === "gate" ? "Signed. Both partners elected the redemption gate." : "Signed. The package executes at the next execution.")}>Sign package</button>
        </div>
      ))}
      {!v.clock.finished && (
        <button type="button" className="ready" disabled={ready} onClick={() => send({ type: "ready", version: v.version }, "")}>
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
          {[...v.orders].reverse().map((o) => (
            <tr key={o.order_id} className={o.forced ? "forced" : ""}>
              <td>{o.forced ? `Broker forced (${o.forced})` : o.order_id}</td>
              <td>{o.side} {num(o.qty)} {o.sym}</td>
              <td className="n">{num(o.filled)}</td>
              <td>{o.status.replaceAll("_", " ").toLowerCase()}</td>
              <td>{o.fills.map((x, i) => <div key={i}>{"rejected" in x ? `Rejected: ${x.rejected}` : `Day ${x.day} ${num(x.qty)} @ ${x.price}`}</div>)}</td>
              <td>{["QUEUED", "PARTIALLY_FILLED"].includes(o.status) && !o.forced && <button type="button" className="link" onClick={() => send({ type: "cancel", order_id: o.order_id }, "Order canceled.")}>Cancel</button>}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {v.packages.length > 0 && (
        <table>
          <thead><tr><th>Package</th><th>Proposed by</th><th>Contents</th><th>Signatures</th><th>Status</th></tr></thead>
          <tbody>
            {v.packages.map((p) => (
              <tr key={p.package_id}>
                <td>{p.digest.slice(0, 10)}</td>
                <td>{v.names[p.proposer]}{p.proposer === me ? " (you)" : ""}</td>
                <td>{p.kind === "gate" ? gateText(p.terms) : p.orders.map((o) => `${o.side} ${o.qty} ${o.sym}`).join(", ")}</td>
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

function gateText(terms: Record<string, unknown>): string {
  const requests = (terms.requests ?? {}) as Record<string, string>;
  return `Gate for the day ${terms.deal_day} dealing close, binding requests: ${Object.entries(requests).sort(([a], [b]) => a.localeCompare(b)).map(([id, units]) => `${id} ${units} units`).join(", ")}. At most 20% of pre-flow NAV is dealt, pro rata; undealt units stay invested and carry forward.`;
}

function Investors({ v, send }: { v: View; send: Send }) {
  const inbox = v.role === "mp" ? v.investors : null;
  const requests = Object.fromEntries((inbox?.lps ?? []).filter((lp) => lp.requested_units != null).map((lp) => [lp.id, lp.requested_units]));
  const pendingGates = v.packages.filter((p) => p.kind === "gate" && p.status === "PENDING_APPROVAL");
  const openGate = pendingGates.some((p) => {
    const bound = (p.terms.requests ?? {}) as Record<string, string>;
    return p.terms.deal_day === inbox?.deal_day && Object.keys(bound).length === Object.keys(requests).length &&
      Object.entries(bound).every(([id, units]) => requests[id] === units);
  });
  const canGate = inbox && !v.clock.finished && !inbox.gate_elected && inbox.deal_day != null && v.clock.day <= inbox.deal_day && Object.keys(requests).length > 0;
  return (
    <section className="panel wide">
      <h2>Investor relationships</h2>
      {inbox ? <>
        <p>{inbox.policy}</p>
        {inbox.lps.map((lp) => {
          const reason = v.clock.finished ? "The run has ended." : v.attention?.committed ? "Attention already committed for this window." : v.clock.day > 15 ? "No LP review remains in this window." : lp.contacted ? "Already contacted before the next review." : "";
          return <article key={lp.id}>
            <h3>{lp.id}: {lp.band.replaceAll("_", " ")}</h3>
            {lp.requested_units != null && <p>Redemption request {lp.requested_units} units, dealt at the day {inbox.deal_day} close, payable day {Number(inbox.deal_day) + 1}.</p>}
            {lp.carried_units != null && <p>Carried by a gate: {lp.carried_units} units, still invested.</p>}
            <button type="button" disabled={Boolean(reason)} onClick={() => send({ type: "contact_lp", lp: lp.id }, `Contacted ${lp.id}; attention committed for this window.`)}>Contact {lp.id}</button>
            {reason && <p className="muted">{reason}</p>}
          </article>;
        })}
        {canGate && <p>{gateText({ deal_day: inbox.deal_day, requests })}</p>}
        <button type="button" disabled={!canGate || openGate} onClick={() => send({ type: "propose_gate", package_id: crypto.randomUUID() }, "Gate proposed for your partner's signature.")}>Propose gate</button>
        {inbox.gate_elected && <p>Both partners elected the gate for day {inbox.deal_day}.</p>}
        {openGate && <p>A gate proposal awaits your partner's signature.</p>}
        {canGate && !openGate && pendingGates.length > 0 && <p role="status">The pending gate binds earlier requests. Propose a fresh gate for the current requests; the previous package stays in the record.</p>}
      </> : <p className="muted">The private investor inbox belongs to the managing partner in generated-market rooms. Published redemption notices and gate packages are shared.</p>}
      <table>
        <thead><tr><th>Series</th><th className="n">Units</th><th className="n">Net capital</th><th className="n">NAV per unit</th><th className="n">High-water mark</th><th className="n">Performance provision</th></tr></thead>
        <tbody>
          {v.series.map((s) => (
            <tr key={s.id}><td>{s.id}</td><td className="n">{num(s.units)}</td><td className="n">{money(s.net, 2)}</td>
              <td className="n">{Number(s.nav_per_unit).toFixed(4)}</td><td className="n">{Number(s.hwm).toFixed(2)}</td><td className="n">{money(s.provision, 2)}</td></tr>
          ))}
        </tbody>
      </table>
      <p className="muted">The management company is a separate entity: {money(v.firm.cash)} cash, {money(v.firm.fee_receivable, 2)} fees receivable, {money(v.firm.payroll_payable)} payroll owed. Fees receivable are not spendable until the fund pays them.</p>
    </section>
  );
}

const JOURNAL_WINDOW = 100; // entries in the DOM at once; search still covers every loaded entry

function Ledger({ roomId, token, version }: { roomId: string; token: string; version: number }) {
  const [entity, setEntity] = useState<"fund" | "firm">("fund");
  const [search, setSearch] = useState("");
  const [data, setData] = useState<LedgerPage | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [retry, setRetry] = useState(0);
  const cache = useRef<{ roomId: string; token: string; entity: string; page: LedgerPage } | null>(null);
  useEffect(() => {
    let cancelled = false;
    const previous = cache.current;
    const sameJournal = previous?.roomId === roomId && previous.token === token && previous.entity === entity;
    if (!sameJournal) setData(null);
    setError(null);
    async function refresh() {
      let cursor = sameJournal ? previous.page.next : 0;
      const entries = sameJournal ? [...previous.page.entries] : [];
      // A full page may have a successor. An empty page still refreshes the digest.
      while (!cancelled) {
        const page: LedgerPage = await api(`/api/rooms/${roomId}/ledger?entity=${entity}&after=${cursor}`, token);
        if (cancelled) return;
        if (page.next !== cursor + page.entries.length) throw new Error("Invalid journal cursor");
        entries.push(...page.entries);
        cursor = page.next;
        if (page.entries.length < 1000) {
          const complete = { ...page, entries };
          cache.current = { roomId, token, entity, page: complete };
          setData(complete);
          return;
        }
      }
    }
    refresh().catch((e: unknown) => {
      if (!cancelled) setError(e instanceof Error ? e.message : "Journal unavailable");
    });
    return () => { cancelled = true; };
  }, [roomId, token, entity, version, retry]);
  const entries = useMemo(() => {
    const query = search.trim().toLowerCase();
    return (data ? [...data.entries].reverse() : []).filter((entry) => !query ||
      [entry.date, entry.id, entry.memo, ...entry.postings.map(([account]) => account)]
        .some((value) => value.toLowerCase().includes(query)));
  }, [data, search]);
  // Render one window of the newest-first matches. A reader on an older window keeps the same entries
  // when new ones arrive; switching journal or search returns to the newest.
  const [start, setStart] = useState(0);
  const seen = useRef({ view: "", count: 0 });
  useEffect(() => {
    const view = `${roomId}|${entity}|${search}`;
    const grew = seen.current.view === view ? entries.length - seen.current.count : 0;
    const changed = seen.current.view !== view;
    seen.current = { view, count: entries.length };
    setStart((s) => (changed ? 0 : s > 0 && grew > 0 ? s + grew : s));
  }, [entries, roomId, entity, search]);
  const first = start < entries.length ? start : Math.max(0, entries.length - JOURNAL_WINDOW);
  const visible = entries.slice(first, first + JOURNAL_WINDOW);
  return (
    <section className="panel wide ledger">
      <div className="row">
        <button type="button" aria-pressed={entity === "fund"} className={entity === "fund" ? "on" : "secondary"} onClick={() => setEntity("fund")}>Fund journal</button>
        <button type="button" aria-pressed={entity === "firm"} className={entity === "firm" ? "on" : "secondary"} onClick={() => setEntity("firm")}>Management company journal</button>
        {data && <span className="digest" title="SHA-256 over every entry; identical inputs replay to the same hash">Journal hash {data.digest.slice(0, 16)}</span>}
      </div>
      <label>Search journal
        <input type="search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Date, entry or account" />
      </label>
      {!data && !error && <p role="status">Loading journal entries…</p>}
      {data && entries.length > 0 && <div className="row">
        <p className="muted" role="status">
          Showing {num(first + 1)}–{num(first + visible.length)} of {num(entries.length)}{" "}
          {search.trim() ? `matching entries (${num(data.entries.length)} loaded)` : "journal entries"}, newest first.
        </p>
        <button type="button" className="secondary" disabled={first === 0}
          onClick={() => setStart(Math.max(0, first - JOURNAL_WINDOW))}>Newer entries</button>
        <button type="button" className="secondary" disabled={first + JOURNAL_WINDOW >= entries.length}
          onClick={() => setStart(first + JOURNAL_WINDOW)}>Older entries</button>
      </div>}
      {data && entries.length === 0 && <p role="status">{search.trim() ? "No journal entries match your search." : "No journal entries yet."}</p>}
      {error && <div>
        <p role="alert">{error}. {data ? "Showing previously loaded entries." : "Journal could not be loaded."}</p>
        <button type="button" onClick={() => setRetry((value) => value + 1)}>Retry journal</button>
      </div>}
      <table>
        <thead><tr><th>Date</th><th>Entry</th><th>Account</th><th className="n">Debit</th><th className="n">Credit</th></tr></thead>
        <tbody>
          {visible.flatMap((e) =>
            e.postings.map(([acct, amt], i) => (
              <tr key={`${e.id}:${i}`} className={i === 0 ? "entry-start" : ""}>
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

function Debrief({ v, headroom, roomId, token }: { v: View; headroom: number; roomId: string; token: string | null }) {
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
        <dt>Scenario</dt><dd>{o.scenario}</dd>
        <dt>Maximum drawdown</dt><dd>{exactPct(o.max_drawdown) ?? o.max_drawdown}% of NAV per unit, measured at business-day closes</dd>
        {o.generated_days != null && o.stressed_days != null && <>
          <dt>Generated market</dt><dd>{num(o.stressed_days)} stressed days out of {num(o.generated_days)} generated days</dd>
        </>}
        {o.seed_commitment && <>
          <dt>Seed SHA-256</dt><dd className="digest">{o.seed_commitment}</dd>
        </>}
        <dt>Tactical redemption paid</dt><dd>{money(o.redemption_paid, 2)}</dd>
        <dt>Recall resolved by</dt><dd>{o.recall_resolved_by ?? "unresolved"}</dd>
        <dt>Forced actions</dt><dd>{o.forced.length ? o.forced.join("; ") : "none"}</dd>
        <dt>Unpaid or failed</dt><dd>{o.unpaid.length ? o.unpaid.join("; ") : "none"}</dd>
        <dt>Replay proof</dt><dd className="digest">tape {o.tape_digest.slice(0, 12)}, journal {o.journal_digest.slice(0, 12)}</dd>
      </dl>
      {token && <RunRecord v={v} roomId={roomId} token={token} />}
      <h2>How you got here</h2>
      {v.decisions.length === 0 ? <p className="muted">Neither partner acted; the tape and the broker decided.</p> : (
        <ol className="decisions">
          {v.decisions.map((d, i) => (
            <li key={i}>
              <span className="when">Day {d.day}</span>
              <span>{v.names[d.role]} {describe(d)}</span>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}

// `detail` echoes the command the partner sent, so its fields depend on `type`.
type CommandDetail = {
  side?: string; qty?: number; sym?: string; order_id?: string; topic?: string; assignment?: string; location?: string;
  amount?: string; question?: string; forecast?: { calm: string; stressed: string };
  orders?: { side: string; qty: number; sym: string }[];
};

function describe(d: Decision): string {
  const x = d.detail as CommandDetail;
  switch (d.type) {
    case "ticket": return `sent a ticket: ${x.side} ${num(x.qty)} ${x.sym}`;
    case "propose": return `proposed ${(x.orders ?? []).map((o) => `${o.side} ${num(o.qty)} ${o.sym}`).join(", ")}`;
    case "sign": return "countersigned the package";
    case "cancel": return `canceled ${x.order_id}`;
    case "visit": return `took the ${(x.assignment ?? "").replaceAll("_", " ")} assignment at the ${x.location}`;
    case "share_research": return `shared the ${(x.topic ?? "").replaceAll("_", " ")} evidence`;
    case "accept_replacement": return "accepted the 40% replacement borrow";
    case "set_reserve": return `set the treasury reserve to ${money(x.amount)}`;
    case "thesis": return `filed a thesis on ${x.question}: calm ${x.forecast?.calm}, stressed ${x.forecast?.stressed}`;
    default: return d.type;
  }
}

// POST /debrief, generated from the server contract (fundforge.schemas.Debrief).
type Scores = DebriefResponse["research"];

/** One baseline replay feeds research, investor relationships and the omission list. */
function RunRecord({ v, roomId, token }: { v: View; roomId: string; token: string }) {
  const [d, setD] = useState<DebriefResponse | null>(null);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);
  const [loading, setLoading] = useState(true);
  const request = useRef<{ roomId: string; token: string; version: number; attempt: number; result: Promise<DebriefResponse> } | null>(null);
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    setD(null);
    if (!request.current || request.current.roomId !== roomId || request.current.token !== token || request.current.version !== v.version || request.current.attempt !== attempt) {
      request.current = { roomId, token, version: v.version, attempt, result: api(`/api/rooms/${roomId}/debrief`, token, { version: v.version }) };
    }
    request.current.result
      .then((got: DebriefResponse) => { if (!cancelled) { setD(got); setError(""); } })
      .catch((e: unknown) => { if (!cancelled) setError(e instanceof Error ? e.message : "Run record unavailable"); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [roomId, token, v.version, attempt]);
  if (loading) return <p role="status">Loading run record…</p>;
  if (error) return <div><p role="alert">Run record unavailable: {error}</p>
    <button type="button" onClick={() => { setLoading(true); setAttempt(a => a + 1); }}>Retry run record</button></div>;
  if (!d) return null;
  return <><ResearchScores v={v} r={d.research} /><InvestorRecord investors={d.investors} /><Replay v={v} roomId={roomId} token={token} baseline={d} /></>;
}

function InvestorRecord({ investors }: { investors: DebriefResponse["investors"] }) {
  if (!investors) return null;
  return <section aria-labelledby="investor-record-h">
    <h2 id="investor-record-h">Investor relationship record</h2>
    <p className="muted">{investors.policy}. Confidence and drivers are the server&apos;s completed-run record.</p>
    <table aria-label="Final investor relationships">
      <thead><tr><th scope="col">Investor</th><th scope="col">Final band</th><th scope="col" className="n">Confidence</th><th scope="col" className="n">Carried units</th></tr></thead>
      <tbody>{Object.entries(investors.final).map(([lp, final]) => <tr key={lp}>
        <th scope="row">{lp}</th><td>{final.band.replaceAll("_", " ")}</td><td className="n">{final.confidence}</td>
        <td className="n">{investors.carried_units[lp] ?? "0"}</td>
      </tr>)}</tbody>
    </table>
    {investors.checkpoints.length === 0 ? <p className="muted">No relationship checkpoints were recorded.</p> : <>
      <p>Drivers below are changes in confidence points; drawdown and open alerts describe the review evidence.</p>
      <table aria-label="Investor confidence checkpoints">
        <thead><tr><th scope="col">Day</th><th scope="col">Investor</th><th scope="col">Checkpoint</th><th scope="col">Confidence</th><th scope="col">Band</th><th scope="col">Drivers</th></tr></thead>
        <tbody>{investors.checkpoints.map((c, i) => <tr key={`${c.day}:${c.lp}:${c.kind}:${i}`}>
          <td>{c.day}</td><th scope="row">{c.lp}</th><td>{c.kind === "review" ? "Interim review" : "Chapter close"}</td>
          <td>{c.start} → {c.end}</td><td>{c.band.replaceAll("_", " ")}</td>
          <td>{c.kind === "review"
            ? `Drawdown ${c.drawdown} (${c.drawdown_pp} pp below peak); response lag ${c.response_lag} (${c.open_alerts} open alerts); contact ${c.contact}; clamp ${c.clamp}`
            : `Performance ${c.performance}; breaches ${c.breaches}; report ${c.report}; meeting ${c.meeting}; gate ${c.gate}; herding ${c.herding}; overdue payments ${c.overdue}; clamp ${c.clamp}`}</td>
        </tr>)}</tbody>
      </table>
    </>}
  </section>;
}

/** Forecast skill, scored beside P&L and kept out of it. */
function ResearchScores({ v, r }: { v: View; r: Scores }) {
  if (r.theses.length === 0) return null; // authored markets, or no thesis filed
  return (
    <section className="research-scores" aria-labelledby="rs-h">
      <h2 id="rs-h">Research record (separate from P&amp;L)</h2>
      <p className="muted">{r.policy}</p>
      <table aria-label="Regime theses and Brier scores">
        <thead><tr><th scope="col">Question</th><th scope="col">True regime</th><th scope="col">Seat</th>
          <th scope="col" className="n">Calm</th><th scope="col" className="n">Stressed</th><th scope="col" className="n">Brier</th></tr></thead>
        <tbody>
          {r.theses.map((t) => (
            <tr key={`${t.role}:${t.question}`}><th scope="row">{t.question}</th><td>{t.true_regime}</td><td>{v.names[t.role] ?? t.role}</td>
              <td className="n">{t.forecast.calm}</td><td className="n">{t.forecast.stressed}</td><td className="n">{t.brier}</td></tr>
          ))}
        </tbody>
      </table>
      <dl>
        {Object.entries(r.seats).map(([role, s]) => (
          <div key={role}><dt>{v.names[role] ?? role} mean Brier</dt><dd>{s.mean_brier ?? "no theses"} ({s.theses} {s.theses === 1 ? "question" : "questions"})</dd></div>
        ))}
      </dl>
    </section>
  );
}

/** REPLAY: omit one recorded decision, retry the rest of the original log and compare. A hypothetical
 *  branch computed by the server; it never changes the real run. */
function Replay({ v, roomId, token, baseline }: { v: View; roomId: string; token: string; baseline: DebriefResponse }) {
  const [branch, setBranch] = useState<DebriefResponse | null>(null);
  const [loading, setLoading] = useState<number | null>(null);
  const [error, setError] = useState("");
  const choices = baseline.timeline.filter((s) => s.can_omit);
  const omit = (seq: number) => {
    setLoading(seq);
    setError("");
    api(`/api/rooms/${roomId}/debrief`, token, { version: v.version, omit_seq: seq })
      .then((got: DebriefResponse) => setBranch(got))
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "Replay unavailable"))
      .finally(() => setLoading(null));
  };
  const o = branch?.outcome;
  return (
    <section className="replay" aria-labelledby="replay-h">
      <h2 id="replay-h">Replay: what if one decision had not been made?</h2>
      <p className="muted">{baseline.policy}</p>
      {choices.length === 0 ? <p className="muted">No recorded decision can be omitted.</p> : (
        <table aria-label="Decisions you can omit">
          <thead><tr><th scope="col" className="n">#</th><th scope="col">When</th><th scope="col">Partner</th><th scope="col">Decision</th>
            <th scope="col" className="n">NAV change</th><th scope="col">Compare</th></tr></thead>
          <tbody>
            {choices.map((s) => (
              <tr key={s.seq}><td className="n">{s.seq}</td><td>Day {s.before.day} {PHASE_LABEL[s.before.phase] ?? s.before.phase}</td>
                <td>{v.names[s.role] ?? s.role}</td><th scope="row">{s.type.replaceAll("_", " ")}</th><td className="n">{money(s.nav_delta, 2)}</td>
                <td><button type="button" className="link" disabled={loading != null} aria-pressed={branch?.omitted_seq === s.seq}
                  onClick={() => omit(s.seq)}>{loading === s.seq ? "Replaying…" : `Replay without #${s.seq}`}</button></td></tr>
            ))}
          </tbody>
        </table>
      )}
      {error && <p role="alert">Replay unavailable: {error}</p>}
      {branch && o && (
        <div className="branch" role="region" aria-label={`Branch without decision ${branch.omitted_seq}`}>
          <h3>Hypothetical branch without decision #{branch.omitted_seq} (the real run is unchanged)</h3>
          <table aria-label="Real run versus branch">
            <thead><tr><th scope="col">Measure</th><th scope="col" className="n">Real run</th><th scope="col" className="n">Branch</th></tr></thead>
            <tbody>
              <tr><th scope="row">Result</th><td className="n">{branch.source_outcome.label}</td><td className="n">{branch.finished ? o.label : "unfinished"}</td></tr>
              <tr><th scope="row">Ending NAV</th><td className="n">{money(branch.source_outcome.nav, 2)}</td><td className="n">{money(o.nav, 2)}</td></tr>
              <tr><th scope="row">Forced actions</th><td className="n">{branch.source_outcome.forced.length}</td><td className="n">{o.forced.length}</td></tr>
            </tbody>
          </table>
          <p>NAV difference (branch minus real): {money(branch.nav_difference, 2)}.{branch.finished ? "" : " The branch did not reach the ending, so its score is not comparable."}</p>
          {branch.incidents.length > 0 && (
            <ul aria-label="Branch incidents">
              {branch.incidents.map((x, i) => <li key={i}>Day {x.day} {x.code}: {x.text}</li>)}
            </ul>
          )}
          {branch.rejected.length > 0 && (
            <ul aria-label="Decisions rejected in the branch">
              {branch.rejected.map((r) => <li key={r.seq}>#{r.seq} {r.type} rejected in this branch: {r.reason}</li>)}
            </ul>
          )}
        </div>
      )}
    </section>
  );
}
