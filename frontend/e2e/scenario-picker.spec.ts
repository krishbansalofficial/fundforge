import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

// The landing page offers Godot's scenario menu; each choice must reach the server as the room's scenario.

test("the landing page offers the scenarios and sends the one chosen", async ({ page }) => {
  await page.goto("/");
  const select = page.getByLabel("Scenario");
  await expect(select.locator("option")).toHaveCount(5);
  await expect(select).toHaveValue("case1");
  const axe = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze();
  expect(axe.violations.filter((v) => v.impact === "serious" || v.impact === "critical").map((v) => v.id)).toEqual([]);

  for (const key of ["case1-controls", "case1-settlement", "case1-generated", "campaign-v1", "case1"]) {
    await page.goto("/");
    await select.selectOption(key);
    const sent = page.waitForRequest((r) => r.method() === "POST" && new URL(r.url()).pathname === "/api/rooms");
    const created = page.waitForResponse((r) => r.request().method() === "POST" && new URL(r.url()).pathname === "/api/rooms");
    await page.getByRole("button", { name: "Open the fund" }).click();
    expect((await sent).postDataJSON().scenario).toBe(key);
    expect((await created).status()).toBe(201);
    await expect(page.getByRole("link", { name: "Take this seat" })).toHaveCount(2);
  }
});

test("a double-click opens one room", async ({ page }) => {
  let posts = 0;
  page.on("request", (r) => { if (r.method() === "POST" && new URL(r.url()).pathname === "/api/rooms") posts++; });
  await page.goto("/");
  await page.locator("form.open-form button[type=submit]").evaluate((b: HTMLButtonElement) => { b.click(); b.click(); }); // same tick
  await expect(page.getByRole("link", { name: "Take this seat" })).toHaveCount(2);
  expect(posts).toBe(1);
});
