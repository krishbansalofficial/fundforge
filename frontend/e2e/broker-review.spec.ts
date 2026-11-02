import AxeBuilder from "@axe-core/playwright";
import { expect, test, type APIRequestContext, type Page } from "@playwright/test";

// case1-controls: a $100 opening-statement error opens an MP-owned review item. The correction is published
// on day 13, so the MP can accept it from day 14 onward at a decision barrier. Both partners move the clock
// with skip votes (the API, as the terminal spec does); the review itself is clicked in the browser.

async function accessible(page: Page, where: string) {
  const result = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze();
  const serious = result.violations.filter((v) => v.impact === "serious" || v.impact === "critical");
  expect(serious.map((v) => `${where}: ${v.id} at ${v.nodes.map((n) => n.target.join(" ")).join(", ")}`)).toEqual([]);
}

const get = async (request: APIRequestContext, room: string, token: string, what: string) =>
  (await request.get(`/api/rooms/${room}/${what}`, { headers: { Authorization: `Bearer ${token}` } })).json();

test("the MP reviews a broker statement correction in RISK; the PM sees the queue but cannot resolve it", async ({ browser, request }) => {
  const created = await request.post("/api/rooms", { data: { scenario: "case1-controls", pm_name: "Ana", mp_name: "Ben" } });
  expect(created.status()).toBe(201);
  const { room_id: room, tokens } = await created.json();
  for (let step = 0; step < 200; step++) {
    const v = await get(request, room, tokens.pm, "view");
    if (v.clock.day >= 14 && v.clock.next?.phase?.startsWith("EXEC")) break;
    for (const role of ["pm", "mp"] as const) {
      if (!v.ready.includes(role)) {
        await request.post(`/api/rooms/${room}/commands`, {
          headers: { Authorization: `Bearer ${tokens[role]}`, "Idempotency-Key": crypto.randomUUID() },
          data: { type: "ready", version: v.version, skip: true },
        });
      }
    }
  }

  const open = async (role: "pm" | "mp") => {
    const page = await (await browser.newContext()).newPage();
    await page.goto(`/room/${room}#t=${tokens[role]}`);
    await expect(page.getByRole("heading", { name: "Desk feed" })).toBeVisible();
    return page;
  };
  const mp = await open("mp");
  const pm = await open("pm");

  for (const [who, page] of [["MP", mp], ["PM", pm]] as const) {
    await page.getByRole("button", { name: "Terminal", exact: true }).click();
    await page.getByRole("button", { name: "RISK certification" }).click();
    const breaks = page.locator("section[aria-labelledby=breaks-h]");
    await expect(breaks.getByRole("heading", { name: "Control breaks and broker statements" })).toBeVisible();
    await expect(breaks.getByRole("heading", { name: /opening-cash: Open, cash/ })).toBeVisible();
    const history = page.getByRole("table", { name: "opening-cash statement revisions" });
    await expect(history.getByRole("row", { name: /^r2 \(supersedes r1\)/ })).toBeVisible();
    await expect(history.getByRole("row", { name: /^r1/ })).toBeVisible(); // the original stays visible
    if (who === "PM") {
      await expect(page.getByRole("button", { name: "Accept matching correction: opening-cash" })).toHaveCount(0);
    }
    await accessible(page, `${who} RISK (broker review)`);
  }

  // The MP accepts the matching correction; the original evidence stays in the history.
  await mp.getByRole("button", { name: "Accept matching correction: opening-cash" }).click();
  await expect(mp.getByRole("status").filter({ hasText: "Correction reviewed. Original evidence remains in the break history." })).toBeVisible();
  const resolutions = mp.getByRole("list", { name: "opening-cash resolution history" });
  await expect(resolutions).toContainText("accepted revision 2");
  await expect(mp.getByRole("table", { name: "opening-cash statement revisions" }).getByRole("row", { name: /^r1/ })).toBeVisible();
  await expect(mp.getByRole("button", { name: "Accept matching correction: opening-cash" })).toHaveCount(0);
  await accessible(mp, "MP RISK (after review)");

  const after = await get(request, room, tokens.mp, "terminal");
  expect(after.risk.controls.statement_queue[0].resolution_history.at(-1).revision).toBe(2);
});
