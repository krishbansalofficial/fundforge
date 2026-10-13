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

test("journal drains multiple pages, appends new entries and refreshes an empty-page digest", async ({ page, request }) => {
  const d = await desk(page, request);
  let count = 1002;
  let digest = "a".repeat(64);
  const cursors: number[] = [];
  await page.route(`**/api/rooms/${d.room}/ledger?*`, (route) => {
    const after = Number(new URL(route.request().url()).searchParams.get("after"));
    cursors.push(after);
    const next = Math.min(after + 1000, count);
    return route.fulfill({ json: { entity: "fund", digest, next,
      entries: Array.from({ length: next - after }, (_, i) => entry(after + i)) } });
  });
  await d.open();
  const rows = page.locator(".ledger tbody tr");
  await expect(rows).toHaveCount(2 * WINDOW); // bounded DOM: one window of two-posting entries
  await expect(page.getByText("Showing 1–100 of 1,002 journal entries")).toBeVisible();
  // Development Strict Mode may start and cancel an extra initial request.
  expect(cursors.filter((n) => n !== 0)).toEqual([1000]);
  expect(cursors[0]).toBe(0);
  await expect(rows.first()).toContainText("fund entry 1001");
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
  await expect(page.getByText("Showing 1–100 of 1,003 journal entries")).toBeVisible();
  await expect(rows.first()).toContainText("fund entry 1002");
  expect(cursors.at(-1)).toBe(1002);
  await expect(page.locator(".ledger .digest")).toContainText(digest.slice(0, 16));
  digest = "c".repeat(64);
  d.view.version++;
  await expect(page.locator(".ledger .digest")).toContainText(digest.slice(0, 16));
  expect(cursors.at(-1)).toBe(1003);
  await expect(page.getByText("Showing 1–100 of 1,003 journal entries")).toBeVisible();
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

test("failed second page can be retried while the room is paused without losing or duplicating entries", async ({ page, request }) => {
  const d = await desk(page, request);
  let failSecondPage = true;
  const cursors: number[] = [];
  await page.route(`**/api/rooms/${d.room}/ledger?*`, (route) => {
    const after = Number(new URL(route.request().url()).searchParams.get("after"));
    cursors.push(after);
    if (after === 1000 && failSecondPage) {
      return route.fulfill({ status: 503, json: { detail: "Second page unavailable" } });
    }
    const next = Math.min(after + 1000, 1002);
    return route.fulfill({ json: { entity: "fund", digest: "d".repeat(64), next,
      entries: Array.from({ length: next - after }, (_, i) => entry(after + i)) } });
  });
  await d.open();
  await expect(page.locator(".ledger [role=alert]")).toContainText("Second page unavailable");
  await expect(page.locator(".ledger tbody tr")).toHaveCount(0);
  const firstAttemptRequests = cursors.length;
  failSecondPage = false;
  // No version change or economic command: recovery must also work in a paused room.
  await page.getByRole("button", { name: "Retry journal" }).click();
  await expect(page.getByText("Showing 1–100 of 1,002 journal entries")).toBeVisible();
  expect(cursors.slice(firstAttemptRequests)).toEqual([0, 1000]);
  expect(await allMemos(page)).toEqual(Array.from({ length: 1002 }, (_, i) => `fund entry ${1001 - i}`));
  await expect(page.locator(".ledger [role=alert]")).toHaveCount(0);
});

test("new room version supersedes a delayed second page without duplicating the first page", async ({ page, request }) => {
  const d = await desk(page, request);
  let release!: () => void;
  const delayed = new Promise<void>((resolve) => { release = resolve; });
  let delayedRequested = false;
  let newer = false;
  await page.route(`**/api/rooms/${d.room}/ledger?*`, async (route) => {
    const after = Number(new URL(route.request().url()).searchParams.get("after"));
    const obsolete = !newer;
    const count = obsolete ? 1001 : 1003;
    const next = Math.min(after + 1000, count);
    if (after === 1000 && obsolete) { delayedRequested = true; await delayed; }
    await route.fulfill({ json: { entity: "fund", digest: (obsolete ? "a" : "b").repeat(64), next,
      entries: Array.from({ length: next - after }, (_, i) => entry(after + i)) } });
  });
  await d.open();
  await expect.poll(() => delayedRequested).toBe(true);
  newer = true;
  d.view.version++;
  const rows = page.locator(".ledger tbody tr");
  await expect(page.getByText("Showing 1–100 of 1,003 journal entries")).toBeVisible();
  await expect(rows.first()).toContainText("fund entry 1002");
  const finished = page.waitForResponse((r) => r.url().includes("ledger?entity=fund&after=1000"));
  release();
  await finished;
  await expect(page.locator(".ledger .digest")).toContainText("b".repeat(16));
  await expect(page.getByText("Showing 1–100 of 1,003 journal entries")).toBeVisible();
  expect(await allMemos(page)).toEqual(Array.from({ length: 1003 }, (_, i) => `fund entry ${1002 - i}`));
});

test("journal window is bounded, pages search matches and keeps a reader's place when entries arrive", async ({ page, request }) => {
  const d = await desk(page, request);
  let count = 250;
  await page.route(`**/api/rooms/${d.room}/ledger?*`, (route) => {
    const after = Number(new URL(route.request().url()).searchParams.get("after"));
    const next = Math.min(after + 1000, count);
    return route.fulfill({ json: { entity: "fund", digest: "e".repeat(64), next,
      entries: Array.from({ length: next - after }, (_, i) => entry(after + i)) } });
  });
  await d.open();
  const memos = page.locator(".ledger tbody tr.entry-start td:nth-child(2)");
  const newer = page.getByRole("button", { name: "Newer entries" });
  const older = page.getByRole("button", { name: "Older entries" });
  await expect(page.getByText("Showing 1–100 of 250 journal entries")).toBeVisible();
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
  await expect(page.getByText("Showing 1–100 of 255 journal entries")).toBeVisible();
});
