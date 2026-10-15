import { expect, test, type Route } from "@playwright/test";

const record = (policy: string, investors: object | null = null) => ({
  policy, investors, timeline: [], research: { policy: "research-policy", theses: [], seats: {} },
});

for (const optional of [false, true]) test(`completed run record recovers without changing room version (investors ${optional})`, async ({ page, request }) => {
  const created = await request.post("/api/rooms", { data: { pm_name: "Retry PM", mp_name: "Retry MP" } });
  expect(created.status()).toBe(201);
  const { room_id: room, tokens } = await created.json();
  const view = await (await request.get(`/api/rooms/${room}/view`, { headers: { Authorization: `Bearer ${tokens.pm}` } })).json();
  view.clock.finished = true;
  view.outcome = { label: "WIN", nav: "25000000", redemption_paid: "100", recall_resolved_by: "replacement borrow", forced: [], unpaid: [],
    tape_digest: "a".repeat(64), journal_digest: "b".repeat(64), scenario: "generated", max_drawdown: "0" };
  const version = view.version;
  let calls = 0;
  let delayed: Route | null = null;
  let commands = 0;
  await page.route(`**/api/rooms/${room}/commands`, route => { commands++; return route.abort(); });
  await page.route(`**/api/rooms/${room}/view`, route => route.fulfill({ json: view }));
  await page.route(`**/api/rooms/${room}/debrief`, route => {
    calls++;
    expect(route.request().postDataJSON()).toEqual({ version });
    if (calls === 1) return route.fulfill({ status: 503, json: { detail: "Temporary replay failure" } });
    delayed = route;
  });
  await page.goto(`/room/${room}#t=${tokens.pm}`);
  await expect(page.locator(".debrief").getByRole("alert")).toContainText("Temporary replay failure");
  expect(calls).toBe(1);
  await page.getByRole("button", { name: "Retry run record" }).click();
  await expect(page.getByRole("status")).toHaveText("Loading run record…");
  await expect(page.getByRole("button", { name: "Retry run record" })).toHaveCount(0);
  await expect.poll(() => calls).toBe(2);
  await delayed!.fulfill({ json: record("Recovered baseline", optional ? {
    policy: "lp-policy", final: { Tactical: { confidence: "51.25", band: "concerned" } }, checkpoints: [], carried_units: {},
  } : null) });
  await expect(page.getByText("Recovered baseline", { exact: true })).toBeVisible();
  await expect(page.locator(".debrief").getByRole("alert")).toHaveCount(0);
  await expect(page.getByRole("heading", { name: "Investor relationship record" })).toHaveCount(optional ? 1 : 0);
  expect(view.version).toBe(version);
  expect(calls).toBe(2);
  expect(commands).toBe(0);
});

test("a delayed older completed-room record cannot replace a newer version", async ({ page, request }) => {
  const created = await request.post("/api/rooms", { data: { pm_name: "Late PM", mp_name: "Late MP" } });
  const { room_id: room, tokens } = await created.json();
  const view = await (await request.get(`/api/rooms/${room}/view`, { headers: { Authorization: `Bearer ${tokens.pm}` } })).json();
  view.clock.finished = true;
  view.outcome = { label: "WIN", nav: "25000000", redemption_paid: "100", recall_resolved_by: "replacement borrow", forced: [], unpaid: [],
    tape_digest: "a".repeat(64), journal_digest: "b".repeat(64), scenario: "generated", max_drawdown: "0" };
  const calls: Route[] = [];
  await page.route(`**/api/rooms/${room}/view`, route => route.fulfill({ json: view }));
  await page.route(`**/api/rooms/${room}/debrief`, route => { calls.push(route); });
  await page.goto(`/room/${room}#t=${tokens.pm}`);
  await expect.poll(() => calls.length).toBe(1);
  view.version++;
  await expect.poll(() => calls.length).toBe(2);
  await calls[1].fulfill({ json: record("Newest baseline") });
  await expect(page.getByText("Newest baseline", { exact: true })).toBeVisible();
  await calls[0].fulfill({ json: record("Obsolete baseline") });
  await expect(page.getByText("Newest baseline", { exact: true })).toBeVisible();
  await expect(page.getByText("Obsolete baseline", { exact: true })).toHaveCount(0);
  expect(calls).toHaveLength(2);
});
