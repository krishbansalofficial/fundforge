import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

// Arena lobby: one click to a solo game; a host gets a join code, a second browser joins with it, and the
// two partners play one round (both Ready, the clock advances). Every step is a click in the real UI.

test("Play solo opens a seated game against the bot", async ({ page }) => {
  await page.goto("/");
  const axe = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze();
  expect(axe.violations.filter((v) => v.impact === "serious" || v.impact === "critical").map((v) => v.id)).toEqual([]);
  await page.getByRole("button", { name: "Play solo" }).click();
  await expect(page).toHaveURL(/\/room\/[0-9a-f]+$/);  // the seat token left the address bar
  await expect(page.locator("button.ready")).toBeVisible();
});

test("host, join with the code, and play one round together", async ({ browser }) => {
  const host = await (await browser.newContext()).newPage();
  await host.goto("/");
  await host.getByRole("button", { name: "Host co-op" }).click();
  const code = (await host.getByTestId("join-code").textContent())!.trim();
  expect(code).toMatch(/^[A-Z2-9]{6}$/);
  await host.getByRole("link", { name: "Enter as portfolio manager" }).click();

  const guest = await (await browser.newContext()).newPage();
  await guest.goto(`/?join=${code}`);  // the shareable link prefills the code
  await expect(guest.getByLabel("Join code")).toHaveValue(code);
  await guest.getByRole("button", { name: "Join", exact: true }).click();
  await expect(guest).toHaveURL(/\/room\/[0-9a-f]+$/);

  const day = async () => (await host.locator("button.ready").textContent()) ?? "";
  const before = await day();
  await host.locator("button.ready").click();
  await expect(host.locator("button.ready")).toHaveText(/Waiting for/);
  await expect(guest.locator("button.ready")).toBeEnabled();
  await guest.locator("button.ready").click();
  await expect.poll(day, { timeout: 10_000 }).not.toBe(before);  // the round advanced for both

  const reused = await guest.request.post("/api/join", { data: { code } });
  expect(reused.status()).toBe(404);  // single use
});

test("a finished game is verified, ranked, and replayable from the leaderboard", async ({ page, request }) => {
  const room = await (await request.post("/api/rooms", { data: { solo_role: "pm" } })).json();
  const auth = { Authorization: `Bearer ${room.tokens.pm}` };
  for (let i = 0; i < 200; i++) {  // the bot readies itself; drive the human seat to the end over the API
    const v = await (await request.get(`/api/rooms/${room.room_id}/view`, { headers: auth })).json();
    if (v.outcome) break;
    await request.post(`/api/rooms/${room.room_id}/commands`,
      { headers: { ...auth, "Idempotency-Key": `r-${v.version}` }, data: { type: "ready", version: v.version } });
  }
  await page.goto(`/room/${room.room_id}#t=${room.tokens.pm}`);
  await expect(page.getByText(/Verified and ranked with score/)).toBeVisible({ timeout: 20_000 });
  await page.getByRole("link", { name: "Public replay" }).click();
  await page.getByRole("button", { name: "Replay and verify now" }).click();
  await expect(page.getByText("Verified: the command log replays to the same journal digest.")).toBeVisible();

  await page.getByRole("link", { name: "Leaderboard" }).click();
  await expect(page.getByRole("heading", { name: "Leaderboard" })).toBeVisible();
  await expect(page.getByRole("link", { name: /^Replay [0-9a-f]+$/ }).first()).toBeVisible();
  const axe = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze();
  expect(axe.violations.filter((v) => v.impact === "serious" || v.impact === "critical").map((v) => v.id)).toEqual([]);
});

test("the round timer starts and pauses through logged commands, over a live socket", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Play solo" }).click();
  const timer = page.getByLabel("Round timer");
  await expect(timer.getByText(/Live/)).toBeVisible({ timeout: 10_000 });  // presence socket welcomed this seat
  await timer.getByRole("button", { name: "Start timer 1x" }).click();
  await expect(timer.getByText(/Round timer 1x: next window in \d+ s/)).toBeVisible();
  await timer.getByRole("button", { name: "Pause" }).click();
  await expect(timer.getByText("Timer paused: Paused by the portfolio manager.")).toBeVisible();
});
