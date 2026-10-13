import { expect, test } from "@playwright/test";

test("stale gate refusal stays visible and the MP can propose current terms", async ({ browser, request }) => {
  const created = await request.post("/api/rooms", { data: { pm_name: "Gate PM", mp_name: "Gate MP" } });
  expect(created.status()).toBe(201);
  const { room_id: room, tokens } = await created.json();
  const response = await request.get(`/api/rooms/${room}/view`, { headers: { Authorization: `Bearer ${tokens.mp}` } });
  const base = await response.json();
  const views: Record<string, typeof base> = {
    mp: { ...base, role: "mp", clock: { ...base.clock, day: 16 }, investors: {
      policy: "Private LP bands", deal_day: 20, gate_elected: false,
      lps: [{ id: "Tactical", band: "concerned", requested_units: "11.00000000", carried_units: null, contacted: false, first_cutoff: 15 }] } },
    pm: { ...base, role: "pm", clock: { ...base.clock, day: 16 }, investors: null },
  };
  const packages = [{ package_id: "old", proposer: "mp", kind: "gate", status: "PENDING_APPROVAL", signatures: ["mp"],
    orders: [], digest: "a".repeat(64), terms: { deal_day: 20, requests: { Tactical: "10.00000000" } } }];
  const contexts = await Promise.all([browser.newContext(), browser.newContext()]);
  try {
    const [mp, pm] = await Promise.all(contexts.map((c) => c.newPage()));
    for (const [page, role] of [[mp, "mp"], [pm, "pm"]] as const) {
      await page.route(`**/api/rooms/${room}/view`, (route) => route.fulfill({ json: { ...views[role], packages } }));
      await page.route(`**/api/rooms/${room}/commands`, (route) => {
        const cmd = route.request().postDataJSON();
        if (cmd.type === "sign" && cmd.package_id === "old") {
          return route.fulfill({ status: 409, json: { detail: "redemption requests changed since the gate was proposed" } });
        }
        if (cmd.type === "propose_gate") {
          expect(role).toBe("mp");
          packages.push({ ...packages[0], package_id: cmd.package_id, digest: "b".repeat(64),
            terms: { deal_day: 20, requests: { Tactical: "11.00000000" } } });
        } else if (cmd.type === "sign") {
          expect(role).toBe("pm");
          expect(cmd.digest).toBe("b".repeat(64));
          packages[1].status = "ELECTED";
          packages[1].signatures.push("pm");
          views.mp.investors.gate_elected = true;
        } else throw new Error(`Unexpected command ${cmd.type}`);
        views.pm.version++;
        views.mp.version++;
        return route.fulfill({ json: { ok: true } });
      });
      await page.goto(`/room/${room}#t=${tokens[role]}`);
      await page.getByRole("button", { name: "Investors", exact: true }).click();
    }
    await pm.getByRole("button", { name: "Sign package" }).click();
    await expect(pm.getByText("Not done: redemption requests changed since the gate was proposed")).toBeVisible();
    expect(packages[0].signatures).toEqual(["mp"]);
    await expect(mp.getByText(/The pending gate binds earlier requests/)).toBeVisible();
    await mp.getByRole("button", { name: "Propose gate" }).click();
    await expect(mp.getByText("Gate proposed for your partner's signature.")).toBeVisible();
    await expect(mp.getByRole("button", { name: "Propose gate" })).toBeDisabled();
    const fresh = pm.locator(".to-sign").filter({ hasText: "Tactical 11.00000000 units" });
    await fresh.getByRole("button", { name: "Sign package" }).click();
    await expect(mp.getByText("Both partners elected the gate for day 20.")).toBeVisible();
    expect(packages[0].terms.requests.Tactical).toBe("10.00000000");
    expect(packages[0].status).toBe("PENDING_APPROVAL");
  } finally { await Promise.all(contexts.map((c) => c.close())); }
});
