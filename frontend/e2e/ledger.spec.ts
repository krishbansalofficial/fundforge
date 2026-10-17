import { expect, test, type Page, type APIRequestContext } from "@playwright/test";

// Real room/desk layout; controlled journal and view responses exercise browser races without
// manufacturing economic postings or modifying the authoritative room's journal.
async function desk(page: Page, request: APIRequestContext) {
  const created = await request.post("/api/rooms", { data: { pm_name: "Journal PM", mp_name: "Journal MP" } });
  expect(created.status()).toBe(201);
  const { room_id: room, tokens } = await created.json();
  const response = await request.get(`/api/rooms/${room}/view`, { headers: { Authorization: `Bearer ${tokens.pm}` } });
  expect(response.ok()).toBeTruthy();
  const view = await response.json();
  await page.route(`**/api/rooms/${room}/view`, (route) => route.fulfill({ json: view }));
  return { room, view, open: async () => {
    await page.goto(`/room/${room}#t=${tokens.pm}`);
    await page.getByRole("button", { name: "Ledger", exact: true }).click();
  } };
}

const WINDOW = 100; // JOURNAL_WINDOW in desk.tsx: entries rendered at once

/** Every rendered entry memo, newest first, walking the window with the Older button. */
async function allMemos(page: Page) {
  const memos = page.locator(".ledger tbody tr.entry-start td:nth-child(2)");
  const older = page.getByRole("button", { name: "Older entries" });
  const seen: string[] = [];
  for (;;) {
    const shown = await memos.allTextContents();
    expect(shown.length).toBeLessThanOrEqual(WINDOW);
    seen.push(...shown);
    if (await older.isDisabled()) return seen;
    await older.click();
    await expect(memos.first()).not.toHaveText(shown[0]);
  }
}

function entry(n: number, entity = "fund") {
  return { id: `${entity}-${n}`, entity, date: "2026-01-12", memo: `${entity} entry ${n}`,
    postings: [["cash", "1.00"], ["capital", "-1.00"]] };
}

/** The endpoint's contract: no `after` is the newest 1,000 entries; `after` is the 1,000 following it. */
function ledgerPage(after: string | null, count: number, digest: string) {
  const start = after == null ? Math.max(0, count - 1000) : Math.min(Number(after), count);
  const next = Math.min(start + 1000, count);
  return { entity: "fund", digest, next, entries: Array.from({ length: next - start }, (_, i) => entry(start + i)) };
}
const afterOf = (url: string) => new URL(url).searchParams.get("after");

test("journal loads the newest page, loads older pages on demand, appends new entries and refreshes an empty-page digest", async ({ page, request }) => {
  const d = await desk(page, request);
  let count = 1002;
  let digest = "a".repeat(64);
  const cursors: (string | null)[] = [];
  await page.route(`**/api/rooms/${d.room}/ledger?*`, (route) => {
    const after = afterOf(route.request().url());
    cursors.push(after);
    return route.fulfill({ json: ledgerPage(after, count, digest) });
  });
  await d.open();
  const rows = page.locator(".ledger tbody tr");
  await expect(rows).toHaveCount(2 * WINDOW); // bounded DOM: one window of two-posting entries
  await expect(page.getByText("Showing 1–100 of 1,000 loaded journal entries")).toBeVisible();
  await expect(rows.first()).toContainText("fund entry 1001");
  // Development Strict Mode may start and cancel an extra initial request.
  expect(cursors.every((n) => n === null)).toBe(true);
  const loadOlder = page.getByRole("button", { name: /Load older journal entries \(2 not loaded\)/ });
  await loadOlder.click();
  await expect(page.getByText("Showing 1–100 of 1,002 loaded journal entries")).toBeVisible();
  await expect(page.getByRole("button", { name: /Load older journal entries/ })).toHaveCount(0);
  expect(cursors.filter((n) => n !== null)).toEqual(["0"]);
  const search = page.getByRole("searchbox", { name: "Search journal" });
  await search.fill("fund entry 1001");
  await expect(rows).toHaveCount(2);
  await expect(rows.first()).toContainText("fund entry 1001");
  await search.fill("missing account");
  await expect(rows).toHaveCount(0);
  await expect(page.getByText("No journal entries match your search.")).toBeVisible();
  await search.fill("CAPITAL");
  await expect(rows).toHaveCount(2 * WINDOW);
  await expect(page.getByText("of 1,002 matching entries (1,002 loaded)")).toBeVisible();
  await search.fill("");
  count = 1003;
  digest = "b".repeat(64);
  d.view.version++;
  await expect(page.getByText("Showing 1–100 of 1,003 loaded journal entries")).toBeVisible();
  await expect(rows.first()).toContainText("fund entry 1002");
  expect(cursors.at(-1)).toBe("1002");
  await expect(page.locator(".ledger .digest")).toContainText(digest.slice(0, 16));
  digest = "c".repeat(64);
  d.view.version++;
  await expect(page.locator(".ledger .digest")).toContainText(digest.slice(0, 16));
  expect(cursors.at(-1)).toBe("1003");
  await expect(page.getByText("Showing 1–100 of 1,003 loaded journal entries")).toBeVisible();
  expect(cursors.filter((n) => n !== null)).toEqual(["0", "1002", "1003"]); // no page fetched twice
});

test("late fund response cannot overwrite the management company journal", async ({ page, request }) => {
  const d = await desk(page, request);
  let release!: () => void;
  const delayed = new Promise<void>((resolve) => { release = resolve; });
  let fundRequested = false;
  await page.route(`**/api/rooms/${d.room}/ledger?*`, async (route) => {
    const entity = new URL(route.request().url()).searchParams.get("entity")!;
    if (entity === "fund") { fundRequested = true; await delayed; }
    await route.fulfill({ json: { entity, digest: entity.repeat(16), next: 1, entries: [entry(0, entity)] } });
  });
  await d.open();
  await expect.poll(() => fundRequested).toBe(true);
  await page.getByRole("button", { name: "Management company journal" }).click();
  await expect(page.locator(".ledger tbody")).toContainText("firm entry 0");
  const finished = page.waitForResponse((r) => r.url().includes("ledger?entity=fund"));
  release();
  await finished;
  await expect(page.locator(".ledger tbody")).not.toContainText("fund entry");
  await expect(page.locator(".ledger tbody tr")).toHaveCount(2);
  await page.getByRole("button", { name: "Fund journal", exact: true }).click();
  await expect(page.locator(".ledger tbody")).toContainText("fund entry 0");
});

test("failed refresh retains entries and retries from the last committed cursor", async ({ page, request }) => {
  const d = await desk(page, request);
  let fail = false;
  const cursors: number[] = [];
  await page.route(`**/api/rooms/${d.room}/ledger?*`, (route) => {
    const after = Number(new URL(route.request().url()).searchParams.get("after"));
    cursors.push(after);
    if (fail) return route.fulfill({ status: 503, json: { detail: "Journal temporarily unavailable" } });
    return route.fulfill({ json: { entity: "fund", digest: "a".repeat(64), next: after + 1, entries: [entry(after)] } });
  });
  await d.open();
  await expect(page.locator(".ledger tbody tr")).toHaveCount(2);
  fail = true;
  d.view.version++;
  await expect(page.locator(".ledger [role=alert]")).toContainText("Showing previously loaded entries");
  await expect(page.locator(".ledger tbody tr")).toHaveCount(2);
  fail = false;
  d.view.version++;
  await expect(page.locator(".ledger tbody tr")).toHaveCount(4);
  expect(cursors.slice(-2)).toEqual([1, 1]);
  expect(cursors.slice(0, -2).every((n) => n === 0)).toBe(true);
  await expect(page.locator(".ledger [role=alert]")).toHaveCount(0);
});

test("failed older page can be retried while the room is paused without losing or duplicating entries", async ({ page, request }) => {
  const d = await desk(page, request);
  let failOlderPage = true;
  const cursors: (string | null)[] = [];
  await page.route(`**/api/rooms/${d.room}/ledger?*`, (route) => {
    const after = afterOf(route.request().url());
    cursors.push(after);
    if (after === "0" && failOlderPage) {
      return route.fulfill({ status: 503, json: { detail: "Older page unavailable" } });
    }
    return route.fulfill({ json: ledgerPage(after, 1002, "d".repeat(64)) });
  });
  await d.open();
  const loadOlder = page.getByRole("button", { name: /Load older journal entries/ });
  await loadOlder.click();
  await expect(page.locator(".ledger [role=alert]")).toContainText("Older page unavailable");
  await expect(page.getByText("Showing 1–100 of 1,000 loaded journal entries")).toBeVisible();
  failOlderPage = false;
  // No version change or economic command: recovery must also work in a paused room.
  await expect(loadOlder).toBeEnabled();
  await loadOlder.click();
  await expect(page.getByText("Showing 1–100 of 1,002 loaded journal entries")).toBeVisible();
  expect(cursors.filter((n) => n !== null)).toEqual(["0", "0"]);
  expect(await allMemos(page)).toEqual(Array.from({ length: 1002 }, (_, i) => `fund entry ${1001 - i}`));
  await expect(page.locator(".ledger [role=alert]")).toHaveCount(0);
});

test("room advancing while an older page is delayed merges both without duplicates", async ({ page, request }) => {
  const d = await desk(page, request);
  let release!: () => void;
  const delayed = new Promise<void>((resolve) => { release = resolve; });
  let delayedRequested = false;
  let newer = false;
  await page.route(`**/api/rooms/${d.room}/ledger?*`, async (route) => {
    const after = afterOf(route.request().url());
    const obsolete = !newer;
    const json = ledgerPage(after, obsolete ? 1001 : 1003, (obsolete ? "a" : "b").repeat(64));
    if (after === "0") { delayedRequested = true; await delayed; }
    await route.fulfill({ json });
  });
  await d.open();
  const loadOlder = page.getByRole("button", { name: /Load older journal entries/ });
  await loadOlder.click();
  await expect.poll(() => delayedRequested).toBe(true);
  await expect(page.getByRole("button", { name: "Loading older journal entries…" })).toBeDisabled();
  newer = true;
  d.view.version++;
  const rows = page.locator(".ledger tbody tr");
  await expect(page.getByText("Showing 1–100 of 1,002 loaded journal entries")).toBeVisible();
  await expect(rows.first()).toContainText("fund entry 1002");
  const finished = page.waitForResponse((r) => r.url().includes("ledger?entity=fund&after=0"));
  release();
  await finished;
  await expect(page.locator(".ledger .digest")).toContainText("b".repeat(16));
  await expect(page.getByText("Showing 1–100 of 1,003 loaded journal entries")).toBeVisible();
  expect(await allMemos(page)).toEqual(Array.from({ length: 1003 }, (_, i) => `fund entry ${1002 - i}`));
});

test("journal window is bounded, pages search matches and keeps a reader's place when entries arrive", async ({ page, request }) => {
  const d = await desk(page, request);
  let count = 250;
  await page.route(`**/api/rooms/${d.room}/ledger?*`, (route) =>
    route.fulfill({ json: ledgerPage(afterOf(route.request().url()), count, "e".repeat(64)) }));
  await d.open();
  const memos = page.locator(".ledger tbody tr.entry-start td:nth-child(2)");
  const newer = page.getByRole("button", { name: "Newer entries" });
  const older = page.getByRole("button", { name: "Older entries" });
  await expect(page.getByText("Showing 1–100 of 250 loaded journal entries")).toBeVisible();
  await expect(newer).toBeDisabled();
  await older.click();
  await expect(page.getByText("Showing 101–200 of 250")).toBeVisible();
  await expect(memos.first()).toHaveText("fund entry 149");
  await older.click();
  await expect(page.getByText("Showing 201–250 of 250")).toBeVisible(); // windows never overlap
  await expect(memos.last()).toHaveText("fund entry 0");
  await expect(older).toBeDisabled();

  // Five new entries arrive while reading the oldest window: the same entries stay on screen.
  count = 255;
  d.view.version++;
  await expect(page.getByText("Showing 206–255 of 255")).toBeVisible();
  await expect(memos.last()).toHaveText("fund entry 0");
  await newer.click();
  await expect(page.getByText("Showing 106–205 of 255")).toBeVisible();

  // "entry 1" matches 1, 10-19 and 100-199 (111 entries): search pages through all of them from the newest.
  const search = page.getByRole("searchbox", { name: "Search journal" });
  await search.fill("entry 1");
  await expect(page.getByText("Showing 1–100 of 111 matching entries (255 loaded)")).toBeVisible();
  await expect(memos.first()).toHaveText("fund entry 199");
  expect(await allMemos(page)).toEqual([
    ...Array.from({ length: 100 }, (_, i) => `fund entry ${199 - i}`),
    ...Array.from({ length: 10 }, (_, i) => `fund entry ${19 - i}`), "fund entry 1"]);
  await search.fill("");
  await expect(page.getByText("Showing 1–100 of 255 loaded journal entries")).toBeVisible();
});
