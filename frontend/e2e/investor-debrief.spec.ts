import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

for (const mode of ["populated", "absent", "empty"] as const) test(`investor debrief ${mode}: completed record shares one request and stays hidden during play`, async ({ page, request }) => {
  const created = await request.post("/api/rooms", { data: { pm_name: "Record PM", mp_name: "Record MP" } });
  expect(created.status()).toBe(201);
  const { room_id: room, tokens } = await created.json();
  const view = await (await request.get(`/api/rooms/${room}/view`, { headers: { Authorization: `Bearer ${tokens.pm}` } })).json();
  let calls = 0;
  const investors = mode === "absent" ? null : {
    policy: "lp-test-policy", carried_units: { Tactical: "123.45678901" },
    final: { Tactical: { confidence: "42.125", band: "withdrawal_risk" } },
    checkpoints: mode === "empty" ? [] : [
      { day: "15", lp: "Tactical", kind: "review", policy_version: "lp-test-policy", start: "65", end: "58",
        band: "stable", drawdown: "-8", drawdown_pp: "5.00", response_lag: "0", open_alerts: "0", contact: "1", clamp: "0" },
      { day: "20", lp: "Tactical", kind: "chapter_close", policy_version: "lp-test-policy", start: "58", end: "42.125",
        band: "withdrawal_risk", performance: "-0.875", breaches: "0", report: "-5", meeting: "0", gate: "-10", herding: "0", overdue: "0", clamp: "0" },
    ],
  };
  await page.route(`**/api/rooms/${room}/view`, route => route.fulfill({ json: view }));
  await page.route(`**/api/rooms/${room}/debrief`, route => {
    calls++;
    return route.fulfill({ json: { investors, timeline: [], policy: "replay-policy",
      research: { policy: "research-policy", theses: [], seats: {} } } });
  });
  await page.goto(`/room/${room}#t=${tokens.pm}`);
  await page.getByRole("button", { name: "Debrief", exact: true }).click();
  await expect(page.getByText(/The debrief opens after/)).toBeVisible();
  expect(calls).toBe(0);
  await expect(page.getByText("42.125", { exact: true })).toHaveCount(0);
  await expect(page.getByRole("heading", { name: "Investor relationship record" })).toHaveCount(0);
  view.outcome = { label: "WIN", nav: "25000000.00", redemption_paid: "100.00", recall_resolved_by: "replacement borrow",
    forced: [], unpaid: [], tape_digest: "a".repeat(64), journal_digest: "b".repeat(64), scenario: "generated", max_drawdown: "0.01" };
  view.clock.finished = true;
  view.version++;
  await expect(page.getByText("No recorded decision can be omitted.")).toBeVisible();
  expect(calls).toBe(1);
  if (mode === "absent") {
    await expect(page.getByRole("heading", { name: "Investor relationship record" })).toHaveCount(0);
  } else {
    const final = page.getByRole("table", { name: "Final investor relationships" });
    await expect(final).toContainText("withdrawal risk");
    await expect(final).toContainText("42.125");
    await expect(final).toContainText("123.45678901");
    if (mode === "empty") {
      await expect(page.getByText("No relationship checkpoints were recorded.")).toBeVisible();
      await expect(page.getByRole("table", { name: "Investor confidence checkpoints" })).toHaveCount(0);
    } else {
      const checkpoints = page.getByRole("table", { name: "Investor confidence checkpoints" });
      await expect(checkpoints).toContainText("65 → 58");
      await expect(checkpoints).toContainText("Drawdown -8 (5.00 pp below peak)");
      await expect(checkpoints).toContainText("report -5");
      await expect(checkpoints).toContainText("gate -10");
    }
  }
  const result = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze();
  expect(result.violations.filter(v => v.impact === "serious" || v.impact === "critical").map(v => v.id)).toEqual([]);
});
