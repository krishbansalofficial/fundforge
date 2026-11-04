import AxeBuilder from "@axe-core/playwright";
import { expect, test, type APIRequestContext, type Page } from "@playwright/test";
import { readFileSync } from "node:fs";

// The card exists on a completed run only, every row is a server field (same rows as Godot CardRules.rows),
// the PNG is drawn in the browser and the text goes to the clipboard. Nothing is uploaded.

async function accessible(page: Page, where: string) {
  const result = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze();
  const serious = result.violations.filter((v) => v.impact === "serious" || v.impact === "critical");
  expect(serious.map((v) => `${where}: ${v.id} at ${v.nodes.map((n) => n.target.join(" ")).join(", ")}`)).toEqual([]);
}

const get = async (request: APIRequestContext, room: string, token: string, what: string) =>
  (await request.get(`/api/rooms/${room}/${what}`, { headers: { Authorization: `Bearer ${token}` } })).json();

async function finish(request: APIRequestContext, room: string, tokens: Record<string, string>) {
  for (let step = 0; step < 400; step++) {
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

/** The offsite request guard: while the card is used, the page talks only to its own origin. */
function sameOriginOnly(page: Page, origin: string) {
  const offsite: string[] = [];
  page.on("request", (r) => { if (/^https?:/.test(r.url()) && new URL(r.url()).origin !== origin) offsite.push(r.url()); });
  return offsite;
}

async function checkCard(page: Page, request: APIRequestContext, room: string, tokens: Record<string, string>, out: string) {
  const card = page.locator("section.ending-card");
  await expect(card.getByRole("heading", { name: "Ending card" })).toBeVisible({ timeout: 30_000 });
  const outcome = (await get(request, room, tokens.pm, "view")).outcome;
  const verify = await get(request, room, tokens.pm, "verify");
  const table = card.getByRole("table", { name: "Ending card" });
  await expect(table.getByRole("row", { name: /^Partners/ })).toContainText("(PM) and");
  await expect(table.getByRole("row", { name: /^Result/ })).toContainText(`#${outcome.rank} of ${outcome.funds} funds`);
  await expect(table.getByRole("row", { name: /^Scenario/ })).toContainText(outcome.scenario);
  await expect(table.getByRole("row", { name: /^Forced actions/ })).toContainText(String(outcome.forced.length));
  await expect(table.getByRole("row", { name: /^Journal/ })).toContainText(outcome.journal_digest);
  await expect(table.getByRole("row", { name: /^Chain head/ })).toContainText(verify.chain_head);
  await expect(table.getByRole("row", { name: /^Rules/ })).toContainText(verify.rules_version);
  await accessible(page, `ending card (${outcome.scenario})`);

  const download = page.waitForEvent("download");
  await card.getByRole("button", { name: "Download PNG" }).click();
  const file = await download;
  expect(file.suggestedFilename()).toBe(`fundforge-${outcome.scenario}-${outcome.label.toLowerCase()}.png`);
  await file.saveAs(out);
  const png = readFileSync(out);
  expect(png.subarray(1, 4).toString("ascii")).toBe("PNG");
  expect([png.readUInt32BE(16), png.readUInt32BE(20)]).toEqual([1200, 630]); // IHDR width and height
  await expect(card.getByRole("status")).toHaveText("Card downloaded.");

  await card.getByRole("button", { name: "Copy text" }).focus(); // keyboard path
  await page.keyboard.press("Enter");
  await expect(card.getByRole("status")).toHaveText("Card text copied.");
  const copied = await page.evaluate(() => navigator.clipboard.readText());
  expect(copied).toContain(`Journal: ${outcome.journal_digest}`);
  expect(copied).toContain("Fictional fund; no real money.");
  return { outcome, copied };
}

test("a campaign started from the landing page is playable and ends in the card", async ({ page, request, context, baseURL }, info) => {
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  const offsite = sameOriginOnly(page, new URL(baseURL!).origin);
  await page.goto("/");
  await page.getByLabel("Scenario").selectOption("campaign-v1");
  await page.getByLabel("Portfolio manager").fill("Camp PM");
  await page.getByLabel("Managing partner").fill("Camp MP");
  const created = page.waitForResponse((r) => r.request().method() === "POST" && new URL(r.url()).pathname === "/api/rooms");
  await page.getByRole("button", { name: "Open the fund" }).click();
  const { room_id: room, tokens } = await (await created).json();

  // Before the end: no card, no seed, no verify or debrief call, and the desk works on campaign tickers and days.
  const early: string[] = [];
  page.on("request", (r) => { if (/\/(verify|debrief)$/.test(new URL(r.url()).pathname)) early.push(r.url()); });
  await page.goto(`/room/${room}#t=${tokens.pm}`);
  await expect(page.getByRole("heading", { name: "Desk feed" })).toBeVisible();
  await expect(page.locator(".days li.today")).toContainText("Day 1");
  const name = page.locator("form.ticket").getByLabel("Name");
  await expect(name).toHaveValue(/^FF-/);
  await page.locator("form.ticket").getByLabel("Shares").fill("10");
  await page.getByRole("button", { name: "Send ticket" }).click();
  await expect(page.getByText("Ticket queued for the next execution.")).toBeVisible();
  await page.getByRole("button", { name: "Debrief", exact: true }).click();
  await expect(page.locator("section.ending-card")).toHaveCount(0);
  expect(early).toEqual([]);
  expect((await get(request, room, tokens.pm, "view")).outcome).toBeNull();

  await finish(request, room, tokens);
  const { outcome, copied } = await checkCard(page, request, room, tokens, info.outputPath("campaign.png"));
  expect(outcome.scenario).toBe("campaign-v1");
  expect(copied).toContain(`The campaign-v1 run's hidden variant was "${outcome.variant}".`); // rooms draw their variant at random
  await expect(page.locator(".verdict")).not.toHaveText(/^Distress$/);
  await expect(page.locator("section.ending-card")).not.toContainText("day 16");
  await expect(page.locator(".days li.today")).toHaveCount(0);
  await expect(page.locator(".days li").last()).toContainText("Day 31");
  expect(offsite).toEqual([]);
});

test("a completed case1 run shows the card, with no seed rows", async ({ page, request, context }, info) => {
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  const created = await request.post("/api/rooms", { data: { pm_name: "Card PM", mp_name: "Card MP" } });
  expect(created.status()).toBe(201);
  const { room_id: room, tokens } = await created.json();
  await finish(request, room, tokens);
  await page.goto(`/room/${room}#t=${tokens.pm}`);
  await checkCard(page, request, room, tokens, info.outputPath("case1.png"));
  await expect(page.locator("section.ending-card")).not.toContainText("Seed");
  await expect(page.locator("section.ending-card")).toContainText("Card PM (PM) and Card MP (MP)");
});

test("a generated run hides its seed until the end, then the card checks it against the commitment", async ({ page, request, context }, info) => {
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  // No variant: the server draws a gate-accepted seed, exactly as the landing page's request does.
  const created = await request.post("/api/rooms", { data: { scenario: "case1-generated", pm_name: "Seed PM", mp_name: "Seed MP" } });
  expect(created.status(), await created.text()).toBe(201);
  const { room_id: room, tokens } = await created.json();
  await page.goto(`/room/${room}#t=${tokens.pm}`);
  await expect(page.getByRole("heading", { name: "Desk feed" })).toBeVisible();
  await page.getByRole("button", { name: "Debrief", exact: true }).click();
  await expect(page.locator("section.ending-card")).toHaveCount(0);
  const before = await page.locator("body").innerText();
  expect(before).not.toContain("Seed SHA-256");

  await finish(request, room, tokens);
  const { outcome } = await checkCard(page, request, room, tokens, info.outputPath("generated.png"));
  const seed = outcome.variant.slice("seed:".length);
  expect(before).not.toContain(seed); // what the desk showed before the end did not carry the seed
  const table = page.locator("section.ending-card").getByRole("table", { name: "Ending card" });
  await expect(table.getByRole("row", { name: /^Seed\b(?! SHA)/ })).toContainText(seed);
  await expect(table.getByRole("row", { name: /^Seed SHA-256/ })).toHaveText(/[0-9a-f]{64}$/); // a match shows the digest alone
  await expect(table).not.toContainText("does NOT match");
});

test("a commitment that disagrees with the revealed seed is flagged on the card", async ({ page, request }) => {
  const created = await request.post("/api/rooms", { data: { pm_name: "Bad PM", mp_name: "Bad MP" } });
  const { room_id: room, tokens } = await created.json();
  await finish(request, room, tokens);
  const view = await get(request, room, tokens.pm, "view");
  view.outcome = { ...view.outcome, variant: "seed:abc", seed_commitment: "f".repeat(64) };
  await page.route(`**/api/rooms/${room}/view`, (route) => route.fulfill({ json: view }));
  await page.goto(`/room/${room}#t=${tokens.pm}`);
  await expect(page.locator("section.ending-card").getByRole("row", { name: /^Seed SHA-256/ })).toContainText("does NOT match the revealed seed");
});
