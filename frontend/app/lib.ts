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
