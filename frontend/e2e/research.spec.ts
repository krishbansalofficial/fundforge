import AxeBuilder from "@axe-core/playwright";
import { expect, test, type APIRequestContext, type Page, type Route } from "@playwright/test";

// (a) Terminal hardening against a mocked /terminal route in a real case1 room: a "revised" print label,
//     a late response for an older room version never replaces a newer snapshot, and a failed fetch keeps
//     the last snapshot with an alert.
// (b) A pinned generated room: the seat files a regime thesis from the terminal, plays to the end with
//     skip-ready, and the debrief shows the research record with a Brier score beside, not inside, P&L.

async function accessible(page: Page, where: string) {
  const result = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze();
  const serious = result.violations.filter((v) => v.impact === "serious" || v.impact === "critical");
  expect(serious.map((v) => `${where}: ${v.id} at ${v.nodes.map((n) => n.target.join(" ")).join(", ")}`)).toEqual([]);
}

const get = async (request: APIRequestContext, room: string, token: string, what: string) =>
  (await request.get(`/api/rooms/${room}/${what}`, { headers: { Authorization: `Bearer ${token}` } })).json();

const command = (request: APIRequestContext, room: string, token: string, data: object) =>
  request.post(`/api/rooms/${room}/commands`, {
    headers: { Authorization: `Bearer ${token}`, "Idempotency-Key": crypto.randomUUID() }, data,
  });

const print = (period_day: number, revision: number, value: string) =>
  ({ series: "STREET_ACTIVITY", period_day, published_day: period_day + 1 + 3 * revision, revision, value });

const snapshot = (version: number, headline: string, macro = [print(12, 0, "50.1")]) => ({
  version,
  as_of: { event: version, day: 14, date: "2026-03-14", phase: "OPEN_ADMIN" },
  quotes: [{ sym: "MOCK", mark: "10.00", qty: 100000, change_bps: "1.5", since_start_bps: null, borrow_rate: null }],
  history: [], history_truncated: false,
  risk: { nav: "1000000", headroom: "500000", cash: "1000000", restricted_collateral: "0", stress_method: "Mock stress.", stresses: [] },
  news: [{ day: 14, text: headline }],
  macro,
  regime: null,
});

test("terminal: revised label, late responses never replace newer data, failures keep the last snapshot", async ({ page, request }) => {
  const created = await request.post("/api/rooms", { data: { pm_name: "Mock PM", mp_name: "Mock MP" } });
  expect(created.status()).toBe(201);
  const { room_id: room, tokens } = await created.json();

  const calls: Route[] = [];
  let respond: (route: Route, n: number) => Promise<void> = async () => {};
  await page.route("**/api/rooms/*/terminal", async (route) => {
    calls.push(route);
    await respond(route, calls.length);
  });
  const json = (body: object, status = 200) => ({ status, contentType: "application/json", body: JSON.stringify(body) });
  const bump = async (n: number) => {
    expect((await command(request, room, tokens.mp, { type: "say", text: `bump ${n}` })).ok()).toBeTruthy();
    await expect.poll(() => calls.length, { timeout: 10_000 }).toBe(n);
  };

  // 1. A revision is labelled as such, beside its first print; the desk formats counts in en-US.
  respond = (route) => route.fulfill(json(snapshot(1, "first snapshot", [print(12, 0, "50.1"), print(12, 1, "52.7")])));
  await page.goto(`/room/${room}#t=${tokens.pm}`);
  await page.getByRole("button", { name: "Terminal", exact: true }).click();
  const macro = page.getByRole("table", { name: /STREET_ACTIVITY/ });
  await expect(macro.getByRole("row", { name: /52\.7 revised Day 16/ })).toBeVisible();
  await expect(macro.getByRole("row", { name: /50\.1 first print Day 13/ })).toBeVisible();
  await expect(page.getByRole("table", { name: "Market monitor" })).toContainText("100,000");

  // 2. The room version changes while a request is in flight; the newer response lands first and the
  //    late, older one must not replace it.
  let release: () => void = () => {};
  const held = new Promise<void>((r) => { release = r; });
  respond = async (route, n) => {
    if (n === 2) { await held; await route.fulfill(json(snapshot(2, "stale snapshot"))); }
    else await route.fulfill(json(snapshot(3, "newest snapshot")));
  };
  await bump(2);
  await bump(3);
  await expect(page.getByText("newest snapshot")).toBeVisible();
  release();
  await page.waitForTimeout(1000);
  await expect(page.getByText("newest snapshot")).toBeVisible();
  await expect(page.getByText("stale snapshot")).toHaveCount(0);

  // 3. A failed refetch keeps the last snapshot on screen with an alert.
  respond = (route) => route.fulfill(json({ detail: "terminal offline" }, 503));
  await bump(4);
  await expect(page.getByRole("alert").filter({ hasText: "terminal offline" })).toHaveText("terminal offline. Showing the last loaded snapshot.");
  await expect(page.getByText("newest snapshot")).toBeVisible();
  await accessible(page, "terminal (mocked)");
});

test("a generated room: file a regime thesis, play to the end, and read the Brier score in the debrief", async ({ page, request }) => {
  const created = await request.post("/api/rooms", {
    data: { scenario: "case1-generated", pm_name: "Solo", solo_role: "pm", variant: "seed:research-e2e" },
  });
  expect(created.status()).toBe(201);
  const { room_id: room, tokens } = await created.json();
  // Skip-ready until the first STREET_ACTIVITY print opens a research question (the bot readies its side).
  const skipUntil = async (done: () => Promise<boolean>) => {
    for (let step = 0; step < 150; step++) {
      if (await done()) return;
      const v = await get(request, room, tokens.pm, "view");
      if (!v.ready.includes("pm") && !v.clock.finished) await command(request, room, tokens.pm, { type: "ready", version: v.version, skip: true });
      await page.waitForTimeout(250);
    }
    throw new Error("skip-ready loop did not reach its goal");
  };
  await skipUntil(async () => (await get(request, room, tokens.pm, "terminal")).regime != null);
  const { regime } = await get(request, room, tokens.pm, "terminal");

  await page.goto(`/room/${room}#t=${tokens.pm}`);
  await page.getByRole("button", { name: "Terminal", exact: true }).click();
  await expect(page.getByRole("heading", { name: /^Regime research/ })).toBeVisible();
  const probs = page.getByRole("table", { name: "Regime probabilities" });
  await expect(probs).toContainText("not a forecast of prices");
  await expect(probs.getByRole("row", { name: /^Calm/ })).toContainText(regime.posterior.calm);

  const calm = page.getByLabel("Your calm probability");
  const submit = page.getByRole("button", { name: "Submit thesis" });
  await calm.fill("1.5");
  await expect(page.getByText("Enter a number from 0 to 1 with at most 6 decimals.")).toBeVisible();
  await expect(submit).toBeDisabled();
  await calm.fill("0.35");
  await expect(page.getByText("Stressed: 0.65 (1 − calm, exact).")).toBeVisible();
  await submit.click();
  await expect(page.getByText(`Thesis recorded for ${regime.question}.`)).toBeVisible();
  await expect(page.getByText(`Your thesis for ${regime.question}: calm 0.35, stressed 0.65.`)).toBeVisible();
  await accessible(page, "terminal (regime research)");

  await skipUntil(async () => (await get(request, room, tokens.pm, "view")).clock.finished);
  // The desk opens the debrief on its own once the outcome arrives.
  const scores = page.getByRole("table", { name: "Regime theses and Brier scores" });
  await expect(scores).toBeVisible({ timeout: 15_000 });
  const row = scores.getByRole("row", { name: new RegExp(`^${regime.question} `) });
  await expect(row).toContainText("0.35");
  await expect(row.locator("td").last()).toHaveText(/^\d\.\d+$/);
  await expect(page.getByText(/Solo mean Brier/)).toBeVisible();
  await expect(page.getByRole("heading", { name: "Research record (separate from P&L)" })).toBeVisible();
  await accessible(page, "debrief (research)");
});
