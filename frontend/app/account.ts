import type { components } from "./api-types";

type Schemas = components["schemas"];
export type Profile = Schemas["Profile"];
export type LeaderRow = Schemas["LeaderRow"];
export type ResultDetail = Schemas["ResultDetail"];
export type Reverify = Schemas["Reverify"];

const KEY = "ff-session";

/** The account session token, kept in localStorage (the API is same-origin through the Next rewrite). */
export function getSession(): string {
  try {
    return localStorage.getItem(KEY) ?? "";
  } catch {
    return "";
  }
}

export function setSession(token: string | null) {
  try {
    if (token) localStorage.setItem(KEY, token);
    else localStorage.removeItem(KEY);
  } catch {
    /* private mode: the session lasts for this page only */
  }
}

/** JSON call with the account session attached; throws the server's message on failure. */
export async function call<T>(path: string, init: { method?: string; body?: unknown; seat?: string } = {}): Promise<T> {
  const session = getSession();
  const res = await fetch(path, {
    method: init.method ?? (init.body === undefined ? "GET" : "POST"),
    headers: {
      ...(session ? { "X-Session": session } : {}),
      ...(init.seat ? { Authorization: `Bearer ${init.seat}` } : {}),
      ...(init.body === undefined ? {} : { "Content-Type": "application/json", "Idempotency-Key": crypto.randomUUID() }),
    },
    body: init.body === undefined ? undefined : JSON.stringify(init.body),
    cache: "no-store",
  });
  if (res.status === 204) return undefined as T;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(typeof data.message === "string" ? data.message : `Request failed (${res.status})`);
  return data as T;
}
