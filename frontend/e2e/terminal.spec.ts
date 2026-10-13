import AxeBuilder from "@axe-core/playwright";
import { expect, test, type APIRequestContext, type Page } from "@playwright/test";

// The read-only Forge Terminal tab in the web desk, against real rooms: monitor, chart selection,
// published STREET_ACTIVITY prints in a generated room, and axe with no serious/critical WCAG 2 A/AA issues.

async function accessible(page: Page, where: string) {
  const result = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze();
  const serious = result.violations.filter((v) => v.impact === "serious" || v.impact === "critical");
  expect(serious.map((v) => `${where}: ${v.id} at ${v.nodes.map((n) => n.target.join(" ")).join(", ")}`)).toEqual([]);
}

async function openTerminal(page: Page, room: string, token: string) {
  await page.goto(`/room/${room}#t=${token}`);
  await page.getByRole("button", { name: "Terminal", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Forge Terminal" })).toBeVisible();
}

const view = async (request: APIRequestContext, room: string, token: string) =>
  (await request.get(`/api/rooms/${room}/view`, { headers: { Authorization: `Bearer ${token}` } })).json();

test("terminal renders the monitor, chart, fund watch and stresses; symbol selection changes the chart", async ({ page, request }) => {
  const created = await request.post("/api/rooms", { data: { pm_name: "Term PM", mp_name: "Term MP" } });
  expect(created.status()).toBe(201);
  const { room_id: room, tokens } = await created.json();
  await openTerminal(page, room, tokens.pm);

  const monitor = page.getByRole("table", { name: "Market monitor" });
  await expect(monitor.getByRole("columnheader", { name: "Borrow APR" })).toBeVisible();
  const symbols = monitor.getByRole("button", { name: /^Chart / });
  expect(await symbols.count()).toBeGreaterThan(1);
  await expect(page.getByRole("table", { name: "Static stress" }).getByRole("row", { name: /Broad sell-off/ })).toBeVisible();
  await expect(page.getByLabel("Fund watch")).toContainText("Restricted short collateral");
  await expect(page.getByRole("table", { name: /STREET_ACTIVITY/ })).toHaveCount(0); // authored case1 has no macro series

  const chart = page.getByRole("img", { name: /observed marks over/ });
  const first = await symbols.nth(0).textContent();
  await expect(chart).toHaveAttribute("aria-label", new RegExp(`^${first} `));
  await expect(symbols.nth(0)).toHaveAttribute("aria-pressed", "true");
  const second = (await symbols.nth(1).textContent())!;
  await symbols.nth(1).focus(); // keyboard: reach the symbol and press Enter
  await page.keyboard.press("Enter");
  await expect(symbols.nth(1)).toHaveAttribute("aria-pressed", "true");
  await expect(chart).toHaveAttribute("aria-label", new RegExp(`^${second} `));
  await accessible(page, "terminal (case1)");
});

test("a generated room shows published STREET_ACTIVITY prints, newest first, after days advance", async ({ page, request }) => {
  const created = await request.post("/api/rooms", {
    data: { scenario: "case1-generated", pm_name: "Solo", solo_role: "pm", variant: "seed:terminal-e2e" },
  });
  expect(created.status()).toBe(201);
  const { room_id: room, tokens } = await created.json();
  const auth = { Authorization: `Bearer ${tokens.pm}` };
  // Skip ahead; the bot partner readies its side after each of ours.
  for (let step = 0; step < 30; step++) {
    const v = await view(request, room, tokens.pm);
    if (v.clock.finished || v.clock.day >= 16) break;
    if (!v.ready.includes("pm")) {
      await request.post(`/api/rooms/${room}/commands`, {
        headers: { ...auth, "Idempotency-Key": crypto.randomUUID() }, data: { type: "ready", version: v.version, skip: true },
      });
    }
    await page.waitForTimeout(500);
  }
  await openTerminal(page, room, tokens.pm);
  const macro = page.getByRole("table", { name: /STREET_ACTIVITY/ });
  await expect(macro).toBeVisible();
  const rows = macro.locator("tbody tr");
  expect(await rows.count()).toBeGreaterThan(1);
  await expect(rows.first()).toContainText(/first print|revised/);
  const days = (await rows.locator("th").allTextContents()).map((s) => Number(s.replace("Day ", "")));
  expect(days).toEqual([...days].sort((a, b) => b - a));
  await accessible(page, "terminal (generated)");
});
