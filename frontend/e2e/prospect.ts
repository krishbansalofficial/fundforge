import { expect, type APIRequestContext, type Browser, type Page } from "@playwright/test";

// Shared setup for the campaign prospect specs. The API only plays the setup that backend/tests/test_prospect.py
// uses (two managing-partner prospect assignments before the day 15 condition close, then ready through day 19 for
// the day 20 dealing close); the decisions under test are made in the browser. `tokens` holds one entry per human
// seat, so a solo room (the bot readies its own side) uses the same helpers.

export type View = { version: number; ready: string[]; clock: { day: number; finished: boolean; next: { phase: string } | null };
  prospect: { stage: string; reason: string | null; escrow: string; authorized: string | null } | null;
  series: { id: string; units: string }[]; chat: { role: string; text: string; ref?: string }[];
  packages: { kind: string; status: string }[] };
export type Tokens = Record<string, string>;

const auth = (token: string) => ({ Authorization: `Bearer ${token}` });
export const view = async (request: APIRequestContext, room: string, token: string): Promise<View> =>
  (await request.get(`/api/rooms/${room}/view`, { headers: auth(token) })).json();
const command = async (request: APIRequestContext, room: string, token: string, data: object) =>
  request.post(`/api/rooms/${room}/commands`, { headers: { ...auth(token), "Idempotency-Key": crypto.randomUUID() }, data });

/** Ready every human seat until `done` holds for the managing partner's view (a refused stale ready is simply retried). */
export async function until(request: APIRequestContext, room: string, tokens: Tokens, done: (v: View) => boolean) {
  for (let step = 0; ; step++) {
    const v = await view(request, room, tokens.mp);
    if (done(v)) return v;
    expect(v.clock.finished).toBe(false);
    expect(step).toBeLessThan(400);
    for (const role of Object.keys(tokens)) if (!v.ready.includes(role)) await command(request, room, tokens[role], { type: "ready", version: v.version });
  }
}

/** A campaign room stopped at the day 19 execution barrier with the prospect funded into escrow. */
export async function eligibleRoom(request: APIRequestContext, seats: object): Promise<{ room: string; tokens: Tokens }> {
  const created = await request.post("/api/rooms", { data: { scenario: "campaign-v1", variant: "base", ...seats } });
  expect(created.status(), await created.text()).toBe(201);
  const { room_id: room, tokens } = await created.json();
  // Qualification, then diligence: each is revealed at the next day's mark, both before the day 15 condition close.
  for (const [day, assignment] of [[2, "prospect_qualification"], [3, "prospect_diligence"]] as const) {
    const res = await command(request, room, tokens.mp, { type: "visit", location: "lp", assignment });
    expect(res.ok(), await res.text()).toBe(true);
    await until(request, room, tokens, (v) => v.clock.day >= day);
  }
  expect((await view(request, room, tokens.mp)).prospect?.stage).toBe("diligence");
  // Certified day 15 report -> commitment; day 19 escrow -> eligible. Stop at an execution barrier to decide.
  const eligible = await until(request, room, tokens, (v) => v.clock.day >= 19 && Boolean(v.clock.next?.phase.startsWith("EXEC")));
  expect(eligible.prospect?.stage).toBe("eligible");
  return { room, tokens };
}

/** Each human seat's desk in its own browser context, opened on the Investors tab with the prospect in view. */
export async function investorPages(browser: Browser, room: string, tokens: Tokens): Promise<Record<string, Page>> {
  return Object.fromEntries(await Promise.all(Object.entries(tokens).map(async ([role, token]) => {
    const page = await (await browser.newContext()).newPage();
    await page.goto(`/room/${room}#t=${token}`);
    await expect(page.getByRole("heading", { name: "Committee" })).toBeVisible();
    await page.getByRole("button", { name: "Investors", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Prospective LP: Anchor" })).toBeVisible();
    return [role, page] as const;
  })));
}
