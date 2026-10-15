import type { components, paths } from "./api-types";

// Generated from the server's OpenAPI document (fundforge.schemas); regenerate with `npm run types`.
type Schemas = components["schemas"];
export type View = Schemas["RoomView"];
export type Order = Schemas["Order"];
export type Fill = Schemas["Fill"];
export type RejectedFill = Schemas["RejectedFill"];
export type Package = Schemas["Package"];
export type Outcome = Schemas["Outcome"];
export type Decision = Schemas["Decision"];
export type LedgerPage = Schemas["LedgerPage"];
export type NewRoom = Schemas["NewRoomResponse"];
export type TerminalView = Schemas["TerminalView"];
export type Debrief = Schemas["Debrief"];
export type Forecast = Schemas["Forecast"];
/** Any command `POST /api/rooms/{id}/commands` accepts; `type` selects the shape. */
export type Command = NonNullable<paths["/api/rooms/{room_id}/commands"]["post"]["requestBody"]>["content"]["application/json"];
export type Side = Schemas["OrderSpec"]["side"];

export const money = (s: string | null | undefined, dp = 0) =>
  s == null ? "—" : Number(s).toLocaleString("en-US", { style: "currency", currency: "USD", minimumFractionDigits: dp, maximumFractionDigits: dp });

/** Every count in the desk goes through here: a fixed locale, so no reader sees "1,00,000". */
export const num = (n: number | string | null | undefined) => (n == null ? "—" : Number(n).toLocaleString("en-US"));

/** 1 - p as an exact decimal string, for p in [0, 1] with at most 6 decimals; null if p is not one.
 *  Integer micro-units, never float arithmetic: 1 - "0.3" is "0.7", not "0.7000000000000001". */
export function complement(p: string): string | null {
  const m = /^(0|1)(?:\.(\d{1,6}))?$/.exec(p.trim());
  if (!m) return null;
  const micro = Number(m[1]) * 1_000_000 + Number((m[2] ?? "").padEnd(6, "0"));
  if (micro > 1_000_000) return null;
  const rest = 1_000_000 - micro;
  const frac = String(rest % 1_000_000).padStart(6, "0").replace(/0+$/, "");
  return `${Math.floor(rest / 1_000_000)}${frac ? `.${frac}` : ""}`;
}

/** A decimal-string fraction as an exact percentage string: the point moves two places, so no digit is
 *  rounded or lost ("0.123456" is "12.3456", "-0.0005" is "-0.05"); null if s is not a plain decimal. */
export function exactPct(s: string): string | null {
  const m = /^(-?)(\d+)(?:\.(\d+))?$/.exec(s.trim());
  if (!m) return null;
  const frac = (m[3] ?? "").padEnd(2, "0");
  const int = (m[2] + frac.slice(0, 2)).replace(/^0+(?=\d)/, "");
  const rest = frac.slice(2);
  const out = `${int}${rest ? `.${rest}` : ""}`;
  return m[1] && /[1-9]/.test(out) ? `-${out}` : out;
}

export const pct = (s: string | null | undefined) => (s == null ? "—" : `${(Number(s) * 100).toFixed(1)}%`);

export async function api(path: string, token?: string, body?: unknown, key: string = crypto.randomUUID()) {
  const res = await fetch(path, {
    method: body === undefined ? "GET" : "POST",
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(body === undefined ? {} : { "Content-Type": "application/json", "Idempotency-Key": key }),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
    cache: "no-store",
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(errorMessage(data, res.status));
  return data;
}

const errorMessage = (data: { message?: unknown; detail?: unknown }, status: number) =>
  typeof data.message === "string" ? data.message : typeof data.detail === "string" ? data.detail : `Request failed (${status})`;

/** Poll the room view; null means unchanged since `etag` (HTTP 304), so keep the view already shown. */
export async function fetchView(path: string, token: string, etag: string): Promise<{ view: View; etag: string } | null> {
  const res = await fetch(path, {
    headers: { Authorization: `Bearer ${token}`, ...(etag ? { "If-None-Match": etag } : {}) },
    cache: "no-store",
  });
  if (res.status === 304) return null;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(errorMessage(data, res.status));
  return { view: data, etag: res.headers.get("ETag") ?? "" };
}
