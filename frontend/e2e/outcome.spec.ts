import { expect, test } from "@playwright/test";

for (const generated of [false, true]) test(`completed debrief shows server facts (${generated ? "generated" : "authored"})`, async ({ page, request }) => {
  const created = await request.post("/api/rooms", { data: { pm_name: "Facts PM", mp_name: "Facts MP" } });
  expect(created.status()).toBe(201);
  const { room_id: room, tokens } = await created.json();
  const response = await request.get(`/api/rooms/${room}/view`, { headers: { Authorization: `Bearer ${tokens.pm}` } });
  expect(response.ok()).toBeTruthy();
  const view = await response.json();
  await page.route(`**/api/rooms/${room}/view`, (route) => route.fulfill({ json: view }));
  await page.route(`**/api/rooms/${room}/debrief`, (route) => route.fulfill({ status: 503, json: { detail: "Research scores unavailable" } }));
  await page.goto(`/room/${room}#t=${tokens.pm}`);
  await expect(page.getByRole("heading", { name: "Desk feed" })).toBeVisible();
  await expect(page.getByText("Maximum drawdown", { exact: true })).toHaveCount(0);
  await expect(page.getByText("Seed SHA-256", { exact: true })).toHaveCount(0);
  view.outcome = { label: "WIN", nav: "25000000.00", redemption_paid: "100.00", recall_resolved_by: "replacement borrow",
    forced: [], unpaid: [], tape_digest: "a".repeat(64), journal_digest: "b".repeat(64),
    scenario: generated ? "generated" : "case1", max_drawdown: "0.123456",
    ...(generated ? { generated_days: 10, stressed_days: 0, seed_commitment: "c".repeat(64) } : {}) };
  view.version++;
  await expect(page.locator(".verdict")).toHaveText("Win");
  const facts = page.locator(".debrief dl");
  await expect(facts).toContainText("12.3456% of NAV per unit, measured at business-day closes");
  await expect(facts).toContainText(generated ? "generated" : "case1");
  if (generated) {
    await expect(facts).toContainText("0 stressed days out of 10 generated days");
    await expect(facts).toContainText("c".repeat(64));
  } else {
    await expect(facts).not.toContainText("Generated market");
    await expect(facts).not.toContainText("Seed SHA-256");
  }
});
