import { expect, test, type APIRequestContext, type Page, type Route } from "@playwright/test";

async function setup(page: Page, request: APIRequestContext) {
  const created = await request.post("/api/rooms", { data: { pm_name: "Recovery PM", mp_name: "Recovery MP" } });
  expect(created.status()).toBe(201);
  const { room_id: room, tokens } = await created.json();
  const headers = { Authorization: `Bearer ${tokens.pm}` };
  const view = await (await request.get(`/api/rooms/${room}/view`, { headers })).json();
  const snapshot = await (await request.get(`/api/rooms/${room}/terminal`, { headers })).json();
  snapshot.regime = { question: "regime:3", period_day: 3, evidence: 1, method: "Published evidence.", states: ["calm", "stressed"],
    prior: { calm: "0.5", stressed: "0.5" }, posterior: { calm: "0.5", stressed: "0.5" } };
  let commands = 0;
  await page.route(`**/api/rooms/${room}/view`, route => route.fulfill({ json: view }));
  await page.route(`**/api/rooms/${room}/commands`, route => { commands++; return route.abort(); });
  return { room, tokens, view, snapshot, commands: () => commands };
}

test("paused initial terminal failure retries once without changing room version or issuing commands", async ({ page, request }) => {
  const s = await setup(page, request);
  let calls = 0;
  let pending: Route | null = null;
  await page.route(`**/api/rooms/${s.room}/terminal`, route => {
    calls++;
    if (calls === 1) return route.fulfill({ status: 503, json: { detail: "Initial terminal failure" } });
    pending = route;
  });
  await page.goto(`/room/${s.room}#t=${s.tokens.pm}`);
  await page.getByRole("button", { name: "Terminal", exact: true }).click();
  await expect(page.getByText("Terminal unavailable: Initial terminal failure")).toBeVisible();
  expect(calls).toBe(1);
  const version = s.view.version;
  await page.getByRole("button", { name: "Retry terminal" }).click();
  await expect(page.getByRole("button", { name: "Retry terminal" })).toBeDisabled();
  await expect.poll(() => calls).toBe(2);
  await pending!.fulfill({ json: s.snapshot });
  await expect(page.getByRole("table", { name: "Market monitor" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Retry terminal" })).toHaveCount(0);
  expect(calls).toBe(2);
  expect(s.view.version).toBe(version);
  expect(s.commands()).toBe(0);
});

test("refresh failure keeps terminal page, selected chart and thesis input through retry", async ({ page, request }) => {
  const s = await setup(page, request);
  let calls = 0;
  let pending: Route | null = null;
  await page.route(`**/api/rooms/${s.room}/terminal`, route => {
    calls++;
    if (calls === 1) return route.fulfill({ json: s.snapshot });
    if (calls === 2 || calls === 4) return route.fulfill({ status: 503, json: { detail: "Refresh failure" } });
    pending = route;
  });
  await page.goto(`/room/${s.room}#t=${s.tokens.pm}`);
  await page.getByRole("button", { name: "Terminal", exact: true }).click();
  const symbol = s.snapshot.quotes[1].sym;
  await page.getByRole("button", { name: `Chart ${symbol}`, exact: true }).click();
  await page.getByLabel("Your calm probability").fill("0.42");
  await page.getByRole("button", { name: "ORDERS blotter" }).click();
  s.view.version++;
  await expect(page.getByText("Refresh failure. Showing the last loaded snapshot.")).toBeVisible();
  await expect(page.getByText("Snapshot is stale until refresh succeeds.")).toBeVisible();
  await expect(page.getByRole("button", { name: "ORDERS blotter" })).toHaveAttribute("aria-pressed", "true");
  await page.getByRole("button", { name: "Retry terminal" }).click();
  await expect(page.getByRole("button", { name: "Retry terminal" })).toBeDisabled();
  await expect.poll(() => calls).toBe(3);
  await pending!.fulfill({ json: { ...s.snapshot, version: s.view.version } });
  await expect(page.getByRole("button", { name: "Retry terminal" })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "ORDERS blotter" })).toHaveAttribute("aria-pressed", "true");
  await page.getByRole("button", { name: "MON market monitor" }).click();
  await expect(page.getByRole("button", { name: `Chart ${symbol}`, exact: true })).toHaveAttribute("aria-pressed", "true");
  // Inputs belong to the monitor panel; staying on MON preserves them during data refresh.
  await page.getByLabel("Your calm probability").fill("0.42");
  s.view.version++;
  await expect.poll(() => calls).toBe(4);
  await expect(page.getByText("Refresh failure. Showing the last loaded snapshot.")).toBeVisible();
  await expect(page.getByLabel("Your calm probability")).toHaveValue("0.42");
  await page.getByRole("button", { name: "Retry terminal" }).click();
  await expect.poll(() => calls).toBe(5);
  await pending!.fulfill({ json: { ...s.snapshot, version: s.view.version } });
  await expect(page.getByText("Refreshing terminal…")).toHaveCount(0);
  await expect(page.getByLabel("Your calm probability")).toHaveValue("0.42");
  expect(s.commands()).toBe(0);
});

test("late old-version terminal response cannot overwrite the recovered snapshot", async ({ page, request }) => {
  const s = await setup(page, request);
  const calls: Route[] = [];
  await page.route(`**/api/rooms/${s.room}/terminal`, route => { calls.push(route); });
  await page.goto(`/room/${s.room}#t=${s.tokens.pm}`);
  await page.getByRole("button", { name: "Terminal", exact: true }).click();
  await expect.poll(() => calls.length).toBe(1);
  s.view.version++;
  await expect.poll(() => calls.length).toBe(2);
  await calls[1].fulfill({ json: { ...s.snapshot, version: s.view.version, news: [{ day: 12, text: "Newest terminal record" }] } });
  await expect(page.getByText("Newest terminal record")).toBeVisible();
  await calls[0].fulfill({ json: { ...s.snapshot, news: [{ day: 12, text: "Obsolete terminal record" }] } });
  await expect(page.getByText("Newest terminal record")).toBeVisible();
  await expect(page.getByText("Obsolete terminal record")).toHaveCount(0);
  expect(calls).toHaveLength(2);
});
