import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("MP contacts an LP and both partners elect a gate through the web desk", async ({ browser, request }) => {
  const created = await request.post("/api/rooms", { data: { pm_name: "Inbox PM", mp_name: "Inbox MP", scenario: "case1-generated", variant: "seed:lp-2" } });
  expect(created.status()).toBe(201);
  const { room_id: room, tokens } = await created.json();
  const prefix = `/api/rooms/${room}`;
  const view = async (role: "pm" | "mp") => (await request.get(`${prefix}/view`, { headers: { Authorization: `Bearer ${tokens[role]}` } })).json();
  const command = async (role: "pm" | "mp", data: object) => {
    const response = await request.post(`${prefix}/commands`, { headers: { Authorization: `Bearer ${tokens[role]}`, "Idempotency-Key": crypto.randomUUID() }, data });
    expect(response.ok(), await response.text()).toBeTruthy();
  };
  const pmContext = await browser.newContext();
  const mpContext = await browser.newContext();
  try {
    const pm = await pmContext.newPage();
    const mp = await mpContext.newPage();
    for (const [page, role] of [[pm, "pm"], [mp, "mp"]] as const) {
      await page.goto(`/room/${room}#t=${tokens[role]}`);
      await page.getByRole("button", { name: "Investors", exact: true }).click();
    }
    await expect(pm.getByRole("button", { name: /^Contact / })).toHaveCount(0);
    await expect(pm.getByRole("button", { name: "Propose gate" })).toHaveCount(0);
    await mp.getByRole("button", { name: "Contact Seed", exact: true }).click();
    await expect(mp.getByText("Contacted Seed; attention committed for this window.")).toBeVisible();
    await expect(mp.getByRole("button", { name: "Contact Tactical", exact: true })).toBeDisabled();
    expect((await view("mp")).attention.committed).toBe(true);

    // Drive the deterministic calendar, leaving the tested relationship and approval actions as clicks.
    for (let step = 0; (await view("mp")).clock.day < 16; step++) {
      expect(step).toBeLessThan(40);
      for (const role of ["pm", "mp"] as const) {
        const v = await view(role);
        await command(role, { type: "ready", version: v.version });
      }
    }
    await expect(mp.getByText(/Redemption request .* units, dealt at the day 20 close/)).toBeVisible();
    await expect(pm.getByText(/Tactical: concerned/)).toHaveCount(0);
    await mp.getByRole("button", { name: "Propose gate" }).click();
    await expect(mp.getByText("Gate proposed for your partner's signature.")).toBeVisible();
    await expect(mp.getByRole("button", { name: "Propose gate" })).toBeDisabled();
    await expect(pm.getByText(/Gate for the day 20 dealing close, binding requests: Tactical/)).toBeVisible();
    await expect(mp.getByRole("button", { name: "Sign package" })).toHaveCount(0);
    await pm.getByRole("button", { name: "Sign package" }).click();
    await expect(mp.getByText("Both partners elected the gate for day 20.")).toBeVisible();
    const final = await view("mp");
    expect(final.investors.gate_elected).toBe(true);
    expect(final.packages.find((p: { kind: string }) => p.kind === "gate").signatures.sort()).toEqual(["mp", "pm"]);
    const verified = await request.get(`${prefix}/verify`, { headers: { Authorization: `Bearer ${tokens.pm}` } });
    expect((await verified.json()).ok).toBe(true);
    for (const page of [pm, mp]) {
      const result = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze();
      expect(result.violations.filter((v) => v.impact === "serious" || v.impact === "critical").map((v) => v.id)).toEqual([]);
    }
  } finally {
    await pmContext.close();
    await mpContext.close();
  }
});
