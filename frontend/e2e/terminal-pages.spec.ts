import AxeBuilder from "@axe-core/playwright";
import { expect, test, type APIRequestContext, type Page } from "@playwright/test";

// (a) The server refuses a thesis for a question that is not live; the terminal shows the server's message
//     and keeps the entry. The live question is replaced in a real /terminal snapshot with a stale one.
// (b) A real case1 run with one ticket, skipped to the end: the terminal's ORDERS blotter shows the fills,
//     STREET ranks the funds, and the debrief replays the run without the ticket. axe on each page.

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

test("a thesis for a question that is not live is refused with the server's message", async ({ page, request }) => {
  const created = await request.post("/api/rooms", {
    data: { scenario: "case1-generated", pm_name: "Solo", solo_role: "pm", variant: "seed:thesis-e2e" },
  });
  expect(created.status()).toBe(201);
  const { room_id: room, tokens } = await created.json();
  expect((await get(request, room, tokens.pm, "terminal")).regime).toBeNull(); // no print yet: no live question

  await page.route("**/api/rooms/*/terminal", async (route) => {
    const body = await (await route.fetch()).json();
    body.regime = { question: "regime:3", period_day: 3, evidence: 1, method: "Stale question.", states: ["calm", "stressed"],
      prior: { calm: "0.5", stressed: "0.5" }, posterior: { calm: "0.5", stressed: "0.5" } };
    await route.fulfill({ json: body });
  });
  await page.goto(`/room/${room}#t=${tokens.pm}`);
  await page.getByRole("button", { name: "Terminal", exact: true }).click();
  const calm = page.getByLabel("Your calm probability");
  await calm.fill("0.4");
  await page.getByRole("button", { name: "Submit thesis" }).click();
  await expect(page.getByRole("alert").filter({ hasText: "Thesis not recorded" }))
    .toHaveText("Thesis not recorded: a thesis must answer the terminal's current research question");
  await expect(calm).toHaveValue("0.4");
  await expect(page.getByText("You have no thesis for regime:3 yet.")).toBeVisible();
  await accessible(page, "terminal (refused thesis)");
});

test("ORDERS blotter, STREET league and a debrief replay without the ticket", async ({ page, request }) => {
  const created = await request.post("/api/rooms", { data: { pm_name: "Blot PM", mp_name: "Blot MP" } });
  expect(created.status()).toBe(201);
  const { room_id: room, tokens } = await created.json();
  const ticket = { type: "ticket", order_id: "pm-e2e-blotter", sym: "ALTO", side: "SELL", qty: 1000 };
  expect((await command(request, room, tokens.pm, ticket)).ok()).toBeTruthy();
  for (let step = 0; step < 300; step++) {
    const v = await get(request, room, tokens.pm, "view");
    if (v.clock.finished) break;
    for (const role of ["pm", "mp"] as const) {
      if (!v.ready.includes(role)) await command(request, room, tokens[role], { type: "ready", version: v.version, skip: true });
    }
  }
  expect((await get(request, room, tokens.pm, "view")).clock.finished).toBe(true);

  await page.goto(`/room/${room}#t=${tokens.pm}`);
  const replay = page.getByRole("table", { name: "Decisions you can omit" });
  const row = replay.getByRole("row", { name: /ticket/ });
  await expect(row).toBeVisible({ timeout: 15_000 });
  await accessible(page, "debrief (replay)");
  await row.getByRole("button", { name: /^Replay without #\d+$/ }).click();
  const branch = page.getByRole("region", { name: /^Branch without decision \d+$/ });
  await expect(branch.getByRole("heading")).toContainText("the real run is unchanged");
  await expect(branch).toContainText("NAV difference (branch minus real):");
  await expect(branch.getByRole("table", { name: "Real run versus branch" }).getByRole("row", { name: /^Ending NAV/ })).toBeVisible();
  await accessible(page, "debrief (branch)");

  await page.getByRole("button", { name: "Terminal", exact: true }).click();
  const functions = page.getByRole("navigation", { name: "Terminal functions" });
  const orders = functions.getByRole("button", { name: "ORDERS blotter" });
  await orders.focus(); // keyboard: reach the function and press Enter
  await page.keyboard.press("Enter");
  await expect(orders).toHaveAttribute("aria-pressed", "true");
  const blotter = page.getByRole("table", { name: "Order blotter, newest first" });
  const order = blotter.getByRole("row", { name: /^pm-e2e-blotter ALTO SELL 1,000/ });
  await expect(order).toBeVisible();
  await expect(order).toContainText("Partners");
  await expect(order.locator("ul.fills li").first()).toContainText(/Day \d+ EXEC_[AB]: /);
  await expect(page.getByRole("table", { name: "Market monitor" })).toHaveCount(0);
  await accessible(page, "terminal (orders)");

  await functions.getByRole("button", { name: "STREET league" }).click();
  const league = page.getByRole("table", { name: "Street league table" });
  expect(await league.locator("tbody tr").count()).toBeGreaterThan(1);
  await expect(league.getByRole("row", { name: /Your fund/ })).toBeVisible();
  const ranks = (await league.locator("tbody tr td:first-child").allTextContents()).map(Number);
  expect(ranks).toEqual(ranks.map((_, i) => i + 1));
  await accessible(page, "terminal (street)");
});
