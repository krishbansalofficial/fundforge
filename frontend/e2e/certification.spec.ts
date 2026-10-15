import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

for (const status of ["pending", "certified", "broken"] as const) test(`RISK shows ${status} dealing-close certification`, async ({ page, request }) => {
  const created = await request.post("/api/rooms", { data: { pm_name: "Cert PM", mp_name: "Cert MP" } });
  expect(created.status()).toBe(201);
  const { room_id: room, tokens } = await created.json();
  const snapshot = await (await request.get(`/api/rooms/${room}/terminal`, { headers: { Authorization: `Bearer ${tokens.pm}` } })).json();
  snapshot.risk.certification = { status, certificates: status === "pending" ? [] : [{
    day: 20, date: "2026-01-30", status, independent_nav: "1234567.89", book_nav: "1234567.89",
    difference: "0.00", tolerance: "0.01", reasons: status === "broken" ? ["broker_statement", "payable_residual"] : [],
    strikes: [{ series_id: "Tactical", units: "1000000", net: "1234567.89", nav_per_unit: "1.234568" }],
    redemptions: [{ series_id: "Tactical", units: "100000", nav_per_unit: "1.234568", payable: "123456.80",
      journal_payable: "123456.79", residual: "-0.01", residual_bound: "0.06" }],
  }] };
  await page.route(`**/api/rooms/${room}/terminal`, (route) => route.fulfill({ json: snapshot }));
  await page.goto(`/room/${room}#t=${tokens.pm}`);
  await page.getByRole("button", { name: "Terminal", exact: true }).click();
  await page.getByRole("button", { name: "RISK certification" }).click();
  await expect(page.getByText(`Certificate status: ${status}`, { exact: true })).toBeVisible();
  if (status === "pending") {
    await expect(page.getByText("No dealing-close certificate has been issued yet.")).toBeVisible();
    await expect(page.getByRole("table")).toHaveCount(1); // main desk book, no fabricated certificate
  } else {
    await expect(page.getByRole("table", { name: "Day 20 certified series strikes" })).toContainText("1.234568");
    const residuals = page.getByRole("table", { name: "Day 20 redemption residuals" });
    await expect(residuals).toContainText("-0.01");
    await expect(residuals).toContainText("0.06");
    if (status === "broken") await expect(page.getByText("Certification blocked: broker statement, payable residual")).toBeVisible();
  }
  const axe = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze();
  expect(axe.violations.filter((v) => v.impact === "serious" || v.impact === "critical").map((v) => v.id)).toEqual([]);
});
