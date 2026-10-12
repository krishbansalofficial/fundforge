import AxeBuilder from "@axe-core/playwright";
import { expect, test, type APIRequestContext, type Page } from "@playwright/test";
import { readFileSync } from "node:fs";
import { join } from "node:path";

// Two partners play the designed S2 line through the web desk, each in their own browser context:
// the MP researches borrow at the broker and accepts the replacement loan (so the recall never forces a
// buy-in), the partners cure any announced margin call with an ALTO sale, trim BEAM on day 18, and the
// debrief must say Win. Every action is a click in the real UI; the API is only read, to know the clock.
// Accessibility: axe finds no serious or critical WCAG 2 A/AA violations on the desk or the debrief.

const fixture = JSON.parse(readFileSync(join(__dirname, "../../fixtures/case1.json"), "utf8"));
type Seat = { role: "pm" | "mp"; token: string; page: Page };

async function view(request: APIRequestContext, room: string, token: string) {
  const res = await request.get(`/api/rooms/${room}/view`, { headers: { Authorization: `Bearer ${token}` } });
  expect(res.ok()).toBeTruthy();
  return res.json();
}

/** Click Ready. A page that has not polled since its partner acted is refused as stale (the version
 *  binding working); like a player, wait for the refresh and click again. */
async function ready(request: APIRequestContext, room: string, seat: Seat) {
  for (let attempt = 0; attempt < 6; attempt++) {
    const before = await view(request, room, seat.token);
    if (before.ready.includes(seat.role)) return;
    const button = seat.page.locator("button.ready");
    await expect(button).toBeEnabled();
    await button.click();
    const accepted = await expect
      .poll(async () => {
        const now = await view(request, room, seat.token);
        return now.version > before.version || now.ready.includes(seat.role);
      }, { timeout: 3000 })
      .toBeTruthy()
      .then(() => true, () => false);
    if (accepted) return;
    await seat.page.waitForTimeout(1600); // one poll interval
  }
  throw new Error(`${seat.role} could not mark ready`);
}

async function advanceTo(request: APIRequestContext, room: string, seats: Seat[], day: number, phase: string) {
  for (let step = 0; step < 40; step++) {
    const v = await view(request, room, seats[0].token);
    if (v.clock.next?.day === day && v.clock.next?.phase === phase) return v;
    if (v.clock.finished) throw new Error(`game ended before day ${day} ${phase}`);
    for (const seat of seats) await ready(request, room, seat);
  }
  throw new Error(`never reached day ${day} ${phase}`);
}

async function fresh(seat: Seat, version: number, request: APIRequestContext, room: string) {
  // Wait until this page has polled the current room version (its buttons act on what it shows).
  await expect.poll(async () => (await view(request, room, seat.token)).version).toBe(version);
  await seat.page.waitForTimeout(1600);
}

async function proposeAndSign(request: APIRequestContext, room: string, pm: Seat, mp: Seat,
                              sym: string, side: string, qty: number) {
  const form = pm.page.locator("form.ticket");
  await form.getByLabel("Side").selectOption(side);
  await form.getByLabel("Name").selectOption(sym);
  await form.getByLabel("Shares").fill(String(qty));
  await pm.page.getByRole("button", { name: "Propose to partner" }).click();
  await expect(pm.page.getByText("Package sent for your partner's signature.")).toBeVisible();
  const sign = mp.page.getByRole("button", { name: "Sign package" });
  await expect(sign).toBeVisible({ timeout: 10_000 });
  await sign.click();
  await expect(mp.page.getByText("Signed. The package executes at the next execution.")).toBeVisible();
}

async function accessible(page: Page, where: string) {
  const result = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze();
  const serious = result.violations.filter((v) => v.impact === "serious" || v.impact === "critical");
  expect(serious.map((v) => `${where}: ${v.id} at ${v.nodes.map((n) => n.target.join(" ")).join(", ")}`)).toEqual([]);
}

test("two partners play S2 through the web desk to a Win", async ({ browser, request }) => {
  const created = await request.post("/api/rooms", { data: { pm_name: "Ana", mp_name: "Ben" } });
  expect(created.status()).toBe(201);
  const { room_id: room, tokens } = await created.json();
  const open = async (role: "pm" | "mp"): Promise<Seat> => {
    const page = await (await browser.newContext()).newPage();
    await page.goto(`/room/${room}#t=${tokens[role]}`);
    await expect(page.getByRole("heading", { name: "Desk feed" })).toBeVisible();
    return { role, token: tokens[role], page };
  };
  const pm = await open("pm");
  const mp = await open("mp");
  const seats = [pm, mp];
  await accessible(pm.page, "PM desk");
  await accessible(mp.page, "MP desk");

  // Day 12: the managing partner takes the borrow assignment at the prime broker.
  let v = await advanceTo(request, room, seats, 12, "EXEC_A");
  await fresh(mp, v.version, request, room);
  await mp.page.getByLabel("Research topic").selectOption("borrow");
  await mp.page.getByRole("button", { name: "Assign" }).click();
  await expect(mp.page.getByText(/Attention committed/)).toBeVisible();

  // Day 14: the desk check found a lender; the managing partner accepts the 40% replacement borrow.
  v = await advanceTo(request, room, seats, 14, "EXEC_A");
  await fresh(mp, v.version, request, room);
  await mp.page.getByRole("button", { name: /Accept replacement borrow/ }).click();
  await expect(mp.page.getByText(/Replacement borrow accepted/)).toBeVisible();

  // Day 16: cure an announced margin call with ALTO, sized like the designed line (5x the deficit).
  v = await advanceTo(request, room, seats, 16, "EXEC_A");
  const curedMarginCall = Boolean(v.fund.margin_call);
  if (curedMarginCall) {
    const rows = fixture.margin_schedule.filter((m: { from_day: number }) => m.from_day <= 16);
    const rate = Number(rows[rows.length - 1].maintenance.long);
    const qty = Math.floor((Number(v.fund.margin_call) * 5) / (rate * Number(v.marks.ALTO))) + 1;
    await fresh(pm, v.version, request, room);
    await fresh(mp, v.version, request, room);
    await proposeAndSign(request, room, pm, mp, "ALTO", "SELL", qty);
  }

  // Day 18: trim BEAM before the halt risk and the redemption.
  v = await advanceTo(request, room, seats, 18, "EXEC_A");
  await fresh(pm, v.version, request, room);
  await fresh(mp, v.version, request, room);
  await proposeAndSign(request, room, pm, mp, "BEAM", "SELL", 20000);

  for (let step = 0; step < 40 && !(await view(request, room, pm.token)).clock.finished; step++) {
    for (const seat of seats) await ready(request, room, seat);
  }
  const outcome = (await view(request, room, pm.token)).outcome;
  console.log(`outcome ${outcome.label} in the ${outcome.variant} market, margin call cured: ${curedMarginCall}`);
  expect(outcome.label).toBe("WIN");
  expect(outcome.recall_resolved_by).toBe("replacement borrow");
  for (const seat of seats) {
    await expect(seat.page.locator(".verdict")).toHaveText("Win", { timeout: 10_000 });
    await accessible(seat.page, `${seat.role.toUpperCase()} debrief`);
  }
});
