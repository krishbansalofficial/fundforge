import { expect, test, type APIRequestContext } from "@playwright/test";

// The campaign prospect is admitted through the web desk: the managing partner proposes the admission and the
// portfolio manager countersigns, each in their own browser context. The API only plays the setup that
// backend/tests/test_prospect.py uses (two managing-partner prospect assignments before the day 15 condition
// close, then ready through day 19 for the day 20 dealing close). The variant is pinned (FUNDFORGE_TEST_VARIANTS=1).

type View = { version: number; ready: string[]; clock: { day: number; finished: boolean; next: { phase: string } | null };
  prospect: { stage: string } | null; series: { id: string }[] };

const auth = (token: string) => ({ Authorization: `Bearer ${token}` });
const view = async (request: APIRequestContext, room: string, token: string): Promise<View> =>
  (await request.get(`/api/rooms/${room}/view`, { headers: auth(token) })).json();
const command = async (request: APIRequestContext, room: string, token: string, data: object) =>
  request.post(`/api/rooms/${room}/commands`, { headers: { ...auth(token), "Idempotency-Key": crypto.randomUUID() }, data });
const atExec = (v: View) => Boolean(v.clock.next?.phase.startsWith("EXEC"));

async function readyBoth(request: APIRequestContext, room: string, tokens: Record<string, string>) {
  const v = await view(request, room, tokens.pm);
  for (const role of ["pm", "mp"]) if (!v.ready.includes(role)) await command(request, room, tokens[role], { type: "ready", version: v.version });
}

/** Ready both seats until `done` holds for the managing partner's view (a refused stale ready is simply retried). */
async function until(request: APIRequestContext, room: string, tokens: Record<string, string>, done: (v: View) => boolean) {
  for (let step = 0; ; step++) {
    const v = await view(request, room, tokens.mp);
    if (done(v)) return v;
    expect(v.clock.finished).toBe(false);
    expect(step).toBeLessThan(400);
    await readyBoth(request, room, tokens);
  }
}

async function assign(request: APIRequestContext, room: string, token: string, assignment: string) {
  const res = await command(request, room, token, { type: "visit", location: "lp", assignment });
  expect(res.ok(), await res.text()).toBe(true);
}

test("partners admit the campaign prospect as a new series through the desk", async ({ browser, request }) => {
  const created = await request.post("/api/rooms", { data: { scenario: "campaign-v1", pm_name: "Adm PM", mp_name: "Adm MP", variant: "base" } });
  expect(created.status(), await created.text()).toBe(201);
  const { room_id: room, tokens } = await created.json();

  // Qualification, then diligence: each is revealed at the next day's mark, both before the day 15 condition close.
  await assign(request, room, tokens.mp, "prospect_qualification");
  await until(request, room, tokens, (v) => v.clock.day >= 2);
  await assign(request, room, tokens.mp, "prospect_diligence");
  await until(request, room, tokens, (v) => v.clock.day >= 3);
  expect((await view(request, room, tokens.mp)).prospect?.stage).toBe("diligence");

  // Certified day 15 report -> commitment; day 19 escrow -> eligible. Stop at an execution barrier to consent.
  const eligible = await until(request, room, tokens, (v) => v.clock.day >= 19 && atExec(v));
  expect(eligible.prospect?.stage).toBe("eligible");

  const pages = Object.fromEntries(await Promise.all((["pm", "mp"] as const).map(async (role) => {
    const page = await (await browser.newContext()).newPage();
    await page.goto(`/room/${room}#t=${tokens[role]}`);
    await expect(page.getByRole("heading", { name: "Committee" })).toBeVisible();
    await page.getByRole("button", { name: "Investors", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Prospective LP: Anchor" })).toBeVisible();
    return [role, page] as const;
  })));

  await expect(pages.mp.getByText(/^Funded into escrow outside the fund/)).toBeVisible();
  await pages.mp.getByRole("button", { name: "Propose admission" }).click();
  await expect(pages.mp.getByText("Admission proposed for your partner's signature.")).toBeVisible();

  const ask = pages.pm.locator(".to-sign").filter({ hasText: "Admit Anchor for $5,000,000" });
  await expect(ask).toBeVisible({ timeout: 10_000 });
  await ask.getByRole("button", { name: "Sign package" }).click();
  await expect(pages.pm.getByText("Signed. Both partners consented to the admission.")).toBeVisible();
  await expect(pages.mp.getByText("Both partners consented to admit $5,000,000 at the dealing close.")).toBeVisible({ timeout: 10_000 });

  // Consent is not cash: the series exists only after the day 20 dealing close.
  const after = await until(request, room, tokens, (v) => v.clock.day >= 21);
  expect(after.prospect?.stage).toBe("admitted");
  expect(after.series.map((s) => s.id)).toContain("Anchor");
  for (const page of Object.values(pages)) {
    await expect(page.getByText("Admitted as a new series.")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByRole("cell", { name: "Anchor", exact: true })).toBeVisible();
  }
});
