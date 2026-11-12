import { expect, test } from "@playwright/test";
import { eligibleRoom, investorPages, until, view } from "./prospect";

// The campaign prospect is decided through the web desk, each partner in their own browser context: the managing
// partner proposes an admission amount and the portfolio manager countersigns, or the managing partner declines.
// Expected behaviour follows backend/src/fundforge/investors.py. The variant is pinned (FUNDFORGE_TEST_VARIANTS=1).

const PAIR = { pm_name: "Adm PM", mp_name: "Adm MP" };

test("partners admit the campaign prospect as a new series through the desk", async ({ browser, request }) => {
  const { room, tokens } = await eligibleRoom(request, PAIR);
  const pages = await investorPages(browser, room, tokens);

  await expect(pages.mp.getByText(/^Funded into escrow outside the fund/)).toBeVisible();
  await pages.mp.getByRole("button", { name: "Propose admission" }).click();
  await expect(pages.mp.getByText("Admission proposed for your partner's signature.")).toBeVisible();

  const ask = pages.pm.locator(".to-sign").filter({ hasText: "Admit Anchor for $5,000,000" });
  await expect(ask).toBeVisible({ timeout: 10_000 });
  await ask.getByRole("button", { name: "Sign package" }).click();
  await expect(pages.pm.getByText("Signed. Both partners consented to the admission.")).toBeVisible();
  await expect(pages.mp.getByText("Both partners consented to admit $5,000,000 at the dealing close.")).toBeVisible({ timeout: 10_000 });

  // Consent is not cash: the series exists only after the day 20 dealing close.
  const after = await until(request, room, tokens, (v) => v.clock.day >= 21);
  expect(after.prospect?.stage).toBe("admitted");
  expect(after.series.map((s) => s.id)).toContain("Anchor");
  for (const page of Object.values(pages)) {
    await expect(page.getByText("Admitted as a new series.")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByRole("cell", { name: "Anchor", exact: true })).toBeVisible();
  }
});

test("a smaller amount chosen in the selector is what the partner signs and what is admitted", async ({ browser, request }) => {
  const { room, tokens } = await eligibleRoom(request, PAIR);
  const pages = await investorPages(browser, room, tokens);

  // Every cap_step multiple up to the escrow, largest first; the default is the full escrow.
  const amount = pages.mp.getByRole("combobox", { name: "Admission amount" });
  await expect(amount.locator("option")).toHaveText(["$5,000,000", "$4,000,000", "$3,000,000", "$2,000,000", "$1,000,000"]);
  await expect(amount).toHaveValue("5000000");
  await amount.selectOption("2000000");
  await pages.mp.getByRole("button", { name: "Propose admission" }).click();
  await expect(pages.mp.getByText("Admission proposed for your partner's signature.")).toBeVisible();

  const ask = pages.pm.locator(".to-sign").filter({ hasText: "Admit Anchor for $2,000,000 at the day 20 dealing close" });
  await expect(ask).toBeVisible({ timeout: 10_000 });
  await ask.getByRole("button", { name: "Sign package" }).click();
  for (const page of Object.values(pages)) {
    await expect(page.getByText("Both partners consented to admit $2,000,000 at the dealing close.")).toBeVisible({ timeout: 10_000 });
    // Consent binds an amount; the whole $5,000,000 stays in escrow until the dealing close.
    await expect(page.getByText("$5,000,000 in escrow outside the fund: not NAV, cash or collateral.")).toBeVisible();
  }

  // $2,000,000 at the issue price of 100 is 20,000 units; the unused escrow returns to the LP.
  const after = await until(request, room, tokens, (v) => v.clock.day >= 21);
  expect(after.prospect).toMatchObject({ stage: "admitted", escrow: "0" });
  expect(Number(after.series.find((s) => s.id === "Anchor")?.units)).toBe(20000);
  for (const page of Object.values(pages)) {
    await expect(page.getByText("Admitted as a new series.")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByRole("row").filter({ has: page.getByRole("cell", { name: "Anchor", exact: true }) })
      .getByRole("cell", { name: "20,000", exact: true })).toBeVisible();
    await expect(page.getByText(/in escrow outside the fund/)).toHaveCount(0);
  }
});

test("only the managing partner can decline the prospect, and no series is admitted", async ({ browser, request }) => {
  const { room, tokens } = await eligibleRoom(request, PAIR);
  const pages = await investorPages(browser, room, tokens);

  // The portfolio manager may propose an amount but is offered no decline.
  await expect(pages.pm.getByRole("button", { name: "Propose admission" })).toBeEnabled();
  await expect(pages.pm.getByRole("button", { name: "Decline prospect" })).toHaveCount(0);

  await pages.mp.getByRole("button", { name: "Decline prospect" }).click();
  await expect(pages.mp.getByText("Prospect declined; any escrow returns to it.")).toBeVisible();
  for (const [role, page] of Object.entries(pages)) {
    await expect(page.getByText("The fund declined; any escrow returned to the LP and the fund is unchanged.")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByRole("button", { name: /Propose admission|Decline prospect/ })).toHaveCount(0);
    expect((await view(request, room, tokens[role])).prospect).toMatchObject({ stage: "declined", escrow: "0", authorized: null });
  }

  // Past the day 20 dealing close nothing was admitted and the decline stands.
  const after = await until(request, room, tokens, (v) => v.clock.day >= 21);
  expect(after.prospect?.stage).toBe("declined");
  expect(after.series.map((s) => s.id)).not.toContain("Anchor");
  for (const page of Object.values(pages)) await expect(page.getByRole("cell", { name: "Anchor", exact: true })).toHaveCount(0);
});

test("solo room: the bot partner does not countersign an admission, and the offer lapses", async ({ browser, request }) => {
  const { room, tokens } = await eligibleRoom(request, { mp_name: "Solo MP", solo_role: "mp" });
  const { mp } = await investorPages(browser, room, tokens);

  await mp.getByRole("button", { name: "Propose admission" }).click();
  await expect(mp.getByText("Admission proposed for your partner's signature.")).toBeVisible();

  // The bot answers in the same transaction: it states its refusal in the room chat and leaves the package unsigned.
  const proposed = await view(request, room, tokens.mp);
  expect(proposed.prospect).toMatchObject({ stage: "eligible", authorized: null });
  expect(proposed.packages.filter((p) => p.kind === "admission").map((p) => p.status)).toEqual(["PENDING_APPROVAL"]);
  expect(proposed.chat.some((m) => m.role === "pm" && m.text.includes("human partner"))).toBe(true);
  // What the desk shows of that (the desk renders no chat, so not the bot's reason): the package stays pending
  // approval, no consent is recorded and the proposal stays open.
  await mp.getByRole("button", { name: "Orders and packages", exact: true }).click();
  const pkg = mp.getByRole("row").filter({ hasText: "Admit Anchor for $5,000,000" });
  await expect(pkg.getByRole("cell", { name: "pending approval", exact: true })).toBeVisible();
  await expect(pkg.getByRole("cell", { name: "Solo MP", exact: true })).toBeVisible(); // signatures: only the proposer
  await mp.getByRole("button", { name: "Investors", exact: true }).click();
  await expect(mp.getByText(/^Funded into escrow outside the fund/)).toBeVisible();
  await expect(mp.getByText(/Both partners consented/)).toHaveCount(0);
  await expect(mp.getByRole("button", { name: "Propose admission" })).toBeEnabled();

  // Without consent the offer lapses at the day 20 dealing close.
  const after = await until(request, room, tokens, (v) => v.clock.day >= 21);
  expect(after.prospect).toMatchObject({ stage: "forfeited", reason: "no_consent", escrow: "0" });
  expect(after.series.map((s) => s.id)).not.toContain("Anchor");
  await expect(mp.getByText("The offer lapsed; any escrow returned to the LP and the fund is unchanged. Reason: no consent.")).toBeVisible({ timeout: 15_000 });
});
