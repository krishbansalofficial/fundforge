export type View = any; // mirrors fundforge.governance.Session.view (server is the source of truth)

export const money = (s: string | null | undefined, dp = 0) =>
  s == null ? "—" : Number(s).toLocaleString("en-US", { style: "currency", currency: "USD", minimumFractionDigits: dp, maximumFractionDigits: dp });

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
  if (!res.ok) throw new Error(typeof data.detail === "string" ? data.detail : `Request failed (${res.status})`);
  return data;
}
