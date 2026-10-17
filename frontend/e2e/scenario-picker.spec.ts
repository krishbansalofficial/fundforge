import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

// The landing page offers the scenarios a browser can start (the keys match backend store.SCENARIOS).
// Each choice must reach the server as the room's scenario; the 201 and the seat links prove it was accepted.

async function accessible(page: Page, where: string) {
  const result = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze();
  const serious = result.violations.filter((v) => v.impact === "serious" || v.impact === "critical");
  expect(serious.map((v) => `${where}: ${v.id} at ${v.nodes.map((n) => n.target.join(" ")).join(", ")}`)).toEqual([]);
}

test("the landing page offers the scenarios and sends the one chosen", async ({ page }) => {
  await page.goto("/");
  const select = page.getByLabel("Scenario");
  await expect(select.locator("option")).toHaveCount(4);
  await expect(select.locator("option", { hasText: "Broker review challenge" })).toHaveAttribute("value", "case1-controls");
  await expect(select.locator("option", { hasText: "Campaign" })).toHaveAttribute("value", "campaign-v1");
  await expect(select).toHaveValue("case1");
  await accessible(page, "landing (scenario picker)");

  for (const key of ["case1-controls", "campaign-v1", "case1"]) {
    await page.goto("/");
    await select.selectOption(key);
    await expect(select).toHaveValue(key);
    const sent = page.waitForRequest((r) => r.method() === "POST" && new URL(r.url()).pathname === "/api/rooms");
    const created = page.waitForResponse((r) => r.request().method() === "POST" && new URL(r.url()).pathname === "/api/rooms");
    await page.getByRole("button", { name: "Open the fund" }).click();
    expect((await sent).postDataJSON().scenario).toBe(key);
    expect((await created).status()).toBe(201);
    await expect(page.getByText("The fund is open.")).toBeVisible();
    await expect(page.getByRole("link", { name: "Take this seat" })).toHaveCount(2);
  }
});
