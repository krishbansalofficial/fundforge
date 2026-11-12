import { expect, test, type APIRequestContext } from "@playwright/test";

// The campaign's controlled winddown is proposed and countersigned in the web desk (two browser contexts, one
// per partner). The API then only liquidates the book and clicks Ready, so the run can reach WINDDOWN.
// The market variant is pinned through the API's test-only option (FUNDFORGE_TEST_VARIANTS=1).

const auth = (token: string) => ({ Authorization: `Bearer ${token}` });
const view = async (request: APIRequestContext, room: string, token: string) =>
  (await request.get(`/api/rooms/${room}/view`, { headers: auth(token) })).json();
const command = async (request: APIRequestContext, room: string, token: string, data: object) => {
  const res = await request.post(`/api/rooms/${room}/commands`, { headers: { ...auth(token), "Idempotency-Key": crypto.randomUUID() }, data });
  return res.ok() ? res.json() : null; // a refused command (e.g. a stale ready) is retried by the loop
};
const atExec = (v: { clock: { next: { phase: string } | null } }) => Boolean(v.clock.next?.phase.startsWith("EXEC"));

async function readyBoth(request: APIRequestContext, room: string, tokens: Record<string, string>) {
  const v = await view(request, room, tokens.pm);
  for (const role of ["pm", "mp"]) if (!v.ready.includes(role)) await command(request, room, tokens[role], { type: "ready", version: v.version });
}

test("partners propose and co-sign a campaign winddown in the desk and the run ends in Winddown", async ({ browser, request }) => {
  const created = await request.post("/api/rooms", { data: { scenario: "campaign-v1", pm_name: "Wind PM", mp_name: "Wind MP", variant: "base" } });
  expect(created.status(), await created.text()).toBe(201);
  const { room_id: room, tokens } = await created.json();

  for (let step = 0; !atExec(await view(request, room, tokens.pm)); step++) {
    expect(step).toBeLessThan(10);
    await readyBoth(request, room, tokens);
  }

  const pages = Object.fromEntries(await Promise.all((["pm", "mp"] as const).map(async (role) => {
    const page = await (await browser.newContext()).newPage();
    await page.goto(`/room/${room}#t=${tokens[role]}`);
    await expect(page.getByRole("heading", { name: "Committee" })).toBeVisible();
    return [role, page] as const;
  })));

  // The prospect is on the Investors tab for both seats, with only the stage this seat may know.
  await pages.pm.getByRole("button", { name: "Investors", exact: true }).click();
  await expect(pages.pm.getByRole("heading", { name: /^Prospective LP/ })).toBeVisible();
  await expect(pages.pm.getByRole("button", { name: "Decline prospect" })).toHaveCount(0); // the managing partner's call

  await pages.pm.getByRole("button", { name: "Propose controlled winddown" }).click();
  await expect(pages.pm.getByText("Winddown proposed for your partner's signature.")).toBeVisible();

  const ask = pages.mp.locator(".to-sign").filter({ hasText: "Controlled winddown" });
  await expect(ask).toBeVisible({ timeout: 10_000 });
  await ask.getByRole("button", { name: "Sign package" }).click();
  await expect(pages.mp.getByText("Signed. Both partners declared a controlled winddown.")).toBeVisible();
  await expect(pages.mp.getByRole("button", { name: "Propose controlled winddown" })).toHaveCount(0);
  await expect(pages.pm.getByText("Winddown declared:")).toBeVisible({ timeout: 10_000 });

  // Liquidate through joint packages at each execution barrier, then advance, until the run ends.
  for (let step = 0; step < 400; step++) {
    const v = await view(request, room, tokens.pm);
    if (v.clock.finished) break;
    if (atExec(v)) {
      for (const p of v.positions as { sym: string; qty: number }[]) {
        const open = (v.orders as { sym: string; status: string }[]).some((o) => o.sym === p.sym && ["QUEUED", "PARTIALLY_FILLED"].includes(o.status));
        if (p.qty === 0 || open) continue;
        const id = `liq-${crypto.randomUUID().slice(0, 8)}`;
        const d = await command(request, room, tokens.pm, { type: "propose", package_id: id, orders: [{ order_id: id, sym: p.sym, side: p.qty > 0 ? "SELL" : "COVER", qty: Math.abs(p.qty) }] });
        if (d) await command(request, room, tokens.mp, { type: "sign", package_id: id, digest: d.digest });
      }
    }
    await readyBoth(request, room, tokens);
  }
  const end = await view(request, room, tokens.pm);
  expect(end.clock.finished).toBe(true);
  expect(end.outcome.label).toBe("WINDDOWN");
  await expect(pages.pm.locator(".verdict")).toHaveText("Winddown", { timeout: 15_000 });
});
