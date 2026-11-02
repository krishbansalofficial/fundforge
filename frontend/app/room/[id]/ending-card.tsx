"use client";

import { useEffect, useState } from "react";
import { cardRows, cardText, label, marketText, type Row, type Verify } from "../../card";
import { api, type Debrief, type Outcome } from "../../lib";

const SIZE = { width: 1200, height: 630 }; // CardRules.SIZE
const TONE: Record<string, string> = { WIN: "#6cbf8f", RENEWAL: "#6cbf8f", SURVIVAL: "#e0a14a", WINDDOWN: "#e0a14a" };

function savePng(o: Outcome, rows: Row[], done: (message: string) => void) {
  const c = document.createElement("canvas");
  Object.assign(c, SIZE);
  const g = c.getContext("2d");
  if (!g) return done("This browser cannot draw the card.");
  const text = (s: string, x: number, y: number, font: string, color: string) => {
    g.font = font;
    g.fillStyle = color;
    g.fillText(s, x, y, SIZE.width - x - 30);
  };
  g.fillStyle = "#0f1a27";
  g.fillRect(0, 0, SIZE.width, SIZE.height);
  g.strokeStyle = "#f0c27a";
  g.lineWidth = 2;
  g.strokeRect(1, 1, SIZE.width - 2, SIZE.height - 2);
  text("FUNDFORGE  /  fictional fund, no real money", 30, 46, "18px sans-serif", "#8fa5ba");
  text(label(o), 30, 112, "bold 60px sans-serif", TONE[o.label] ?? "#ec6d62");
  text(marketText(o.variant, o.scenario), 30, 146, "18px sans-serif", "#e8e2d4");
  rows.forEach(([k, v], i) => { // at most 14 rows: 180 + 13 * 32 stays on the 630px card
    text(k, 30, 180 + i * 32, "17px sans-serif", "#8fa5ba");
    text(v, 220, 180 + i * 32, "17px monospace", "#e8e2d4");
  });
  c.toBlob((blob) => {
    if (!blob) return done("The card could not be drawn.");
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `fundforge-${o.scenario}-${o.label.toLowerCase()}.png`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
    done("Card downloaded.");
  }, "image/png");
}

/** Rendered only for a completed run. The PNG is drawn locally and the text goes to the clipboard; nothing is uploaded. */
export function EndingCard({ o, names, research, roomId, token, version }: {
  o: Outcome; names: Record<string, string>; research?: Debrief["research"]; roomId: string; token: string; version: number;
}) {
  const [verify, setVerify] = useState<Verify>();
  const [seedHash, setSeedHash] = useState<string>();
  const [status, setStatus] = useState("");
  useEffect(() => {
    let cancelled = false;
    api(`/api/rooms/${roomId}/verify`, token)
      .then((got: Verify) => { if (!cancelled) setVerify(got); })
      .catch(() => { if (!cancelled) setVerify(undefined); }); // optional source: its rows drop, as in Godot
    return () => { cancelled = true; };
  }, [roomId, token, version]);
  const seed = o.variant?.startsWith("seed:") ? o.variant.slice(5) : null;
  useEffect(() => {
    const subtle = globalThis.crypto?.subtle; // undefined on a plain-http origin
    if (seed == null || !subtle) return;
    let cancelled = false;
    subtle.digest("SHA-256", new TextEncoder().encode(seed))
      .then((b) => { if (!cancelled) setSeedHash([...new Uint8Array(b)].map((x) => x.toString(16).padStart(2, "0")).join("")); });
    return () => { cancelled = true; };
  }, [seed]);
  const rows = cardRows(o, names, research, verify, seedHash);
  const copy = () => {
    const blocked = () => setStatus("Copy is blocked here; select the card text instead.");
    if (!navigator.clipboard) return blocked();
    navigator.clipboard.writeText(cardText(o, rows)).then(() => setStatus("Card text copied."), blocked);
  };
  return <section className="ending-card" aria-labelledby="card-h">
    <h2 id="card-h">Ending card</h2>
    <p>{marketText(o.variant, o.scenario)}</p>
    <table aria-labelledby="card-h">
      <tbody>{rows.map(([k, val]) => <tr key={k}><th scope="row">{k}</th><td className={val.length > 40 ? "digest" : undefined}>{val}</td></tr>)}</tbody>
    </table>
    <div className="row">
      <button type="button" onClick={() => savePng(o, rows, setStatus)}>Download PNG</button>
      <button type="button" className="secondary" onClick={copy}>Copy text</button>
    </div>
    {status && <p role="status">{status}</p>}
  </section>;
}
