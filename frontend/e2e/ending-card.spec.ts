import AxeBuilder from "@axe-core/playwright";
import { expect, test, type APIRequestContext, type Page } from "@playwright/test";
import { readFileSync } from "node:fs";

const LABEL: Record<string, string> = { WIN: "Win", SURVIVAL: "Survival", DISTRESS: "Distress" };

// The ending card appears on a completed run record only. Every row is a server field; the PNG is drawn on a
// canvas in the browser, and "Copy text" puts the same rows on the clipboard. A generated run reveals its seed,
// and the card's SHA-256 of that seed must match the server's commitment.

async function accessible(page: Page, where: string) {
  const result = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze();
  const serious = result.violations.filter((v) => v.impact === "serious" || v.impact === "critical");
  expect(serious.map((v) => `${where}: ${v.id} at ${v.nodes.map((n) => n.target.join(" ")).join(", ")}`)).toEqual([]);
}

const get = async (request: APIRequestContext, room: string, token: string, what: string) =>
  (await request.get(`/api/rooms/${room}/${what}`, { headers: { Authorization: `Bearer ${token}` } })).json();

async function finish(request: APIRequestContext, room: string, tokens: Record<string, string>) {
  for (let step = 0; step < 300; step++) {
    const v = await get(request, room, tokens.pm, "view");
    if (v.clock.finished) return;
    for (const role of ["pm", "mp"] as const) {
      if (!v.ready.includes(role)) {
        await request.post(`/api/rooms/${room}/commands`, {
          headers: { Authorization: `Bearer ${tokens[role]}`, "Idempotency-Key": crypto.randomUUID() },
          data: { type: "ready", version: v.version, skip: true },
        });
      }
    }
  }
  throw new Error("run did not finish");
}

test("a completed case1 run shows an ending card that downloads as PNG and copies as text", async ({ page, request, context }) => {
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  const created = await request.post("/api/rooms", { data: { pm_name: "Card PM", mp_name: "Card MP" } });
  expect(created.status()).toBe(201);
  const { room_id: room, tokens } = await created.json();
  await finish(request, room, tokens);

  await page.goto(`/room/${room}#t=${tokens.pm}`);
  const card = page.locator("section.ending-card");
  await expect(card.getByRole("heading", { name: "Ending card" })).toBeVisible({ timeout: 15_000 });
  const outcome = (await get(request, room, tokens.pm, "view")).outcome;
  await expect(card.locator("dl")).toContainText(`#${outcome.rank} of ${outcome.funds} funds`);
  await expect(card.locator("dl")).toContainText("(excess");
  await expect(card.locator("dl")).toContainText("Card PM (PM) and Card MP (MP)");
  await expect(card.locator("dl")).toContainText(outcome.journal_digest);
  await expect(card.locator("dl")).not.toContainText("Seed SHA-256");
  await accessible(page, "ending card (case1)");

  const download = page.waitForEvent("download");
  await card.getByRole("button", { name: "Download PNG" }).click();
  const file = await download;
  expect(file.suggestedFilename()).toMatch(/^fundforge-case1-(win|survival|distress)\.png$/);
  const path = await file.path();
  const bytes = readFileSync(path!);
  expect(bytes.subarray(1, 4).toString("ascii")).toBe("PNG"); // PNG signature
  await expect(card.getByRole("status")).toHaveText("Card downloaded.");

  await card.getByRole("button", { name: "Copy text" }).click();
  await expect(card.getByRole("status")).toHaveText("Card text copied.");
  const copied = await page.evaluate(() => navigator.clipboard.readText());
  expect(copied.split(/\r?\n/)[0]).toBe(`FundForge: ${LABEL[outcome.label]}`); // Windows clipboards use CRLF
  expect(copied).toContain(`Journal: ${outcome.journal_digest}`);
  expect(copied).toContain("Fictional fund; no real money.");
});

test("a generated run reveals its seed and the card checks it against the commitment", async ({ page, request }) => {
  const seed = "seed:e2e-ending-card";
  const created = await request.post("/api/rooms", { data: { scenario: "case1-generated", pm_name: "Seed PM", mp_name: "Seed MP", variant: seed } });
  expect(created.status()).toBe(201);
  const { room_id: room, tokens } = await created.json();
  await finish(request, room, tokens);

  await page.goto(`/room/${room}#t=${tokens.pm}`);
  const card = page.locator("section.ending-card");
  await expect(card.getByRole("heading", { name: "Ending card" })).toBeVisible({ timeout: 15_000 });
  const facts = card.locator("dl");
  await expect(facts).toContainText("e2e-ending-card");
  await expect(facts).toContainText("Seed SHA-256");
  await expect(facts.locator("dd.digest").last()).toHaveText(/^[0-9a-f]{64}$/);
  await expect(facts).not.toContainText("does NOT match");
  await expect(facts).toContainText("case1-generated");
  await accessible(page, "ending card (generated)");
});
