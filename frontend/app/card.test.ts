import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { cardRows, cardText, exactMoney, marketText } from "./card.ts";
import { SCENARIOS, type Debrief, type Outcome } from "./lib.ts";

const base = {
  label: "SURVIVAL", nav: "21806458.8", rank: 6, funds: 6, score: "-303.3", fund_return_bps: "48.1", benchmark_return_bps: "-35.6",
  excess_bps: "83.7", max_drawdown: "0.087654", scenario: "case1-generated", variant: "seed:abc", seed_commitment: "f".repeat(64),
  stressed_days: 0, generated_days: 10, journal_digest: "j".repeat(64), tape_digest: "t", forced: ["x"], unpaid: [], recall_resolved_by: null, redemption_paid: "0",
} as Outcome;
const facts = (rows: [string, string][]) => Object.fromEntries(rows);

// The expected strings are the ones game/tests/run_tests.gd pins for CardRules.rows.
test("card rows match Godot CardRules.rows, formatted only", () => {
  const rows = facts(cardRows(base, { pm: "Ana", mp: "Ben" }, undefined, { rules_version: "r1", chain_head: "abc" }, "f".repeat(64)));
  assert.equal(rows.Partners, "Ana (PM) and Ben (MP)");
  assert.equal(rows.Result, "#6 of 6 funds  /  Score -303.3 bps");
  assert.equal(rows["vs benchmark"], "fund +48.1 bps vs passive book -35.6 bps");
  assert.equal(rows["Final NAV"], "$21,806,458.80");
  assert.equal(rows["Forced actions"], "1");
  assert.equal(rows["Max drawdown"], "8.7654% (NAV per unit, at closes)");
  assert.equal(rows.Scenario, "case1-generated");
  assert.equal(rows["Stressed days"], "0 of 10 generated");
  assert.equal(rows.Seed, "abc");
  assert.equal(rows["Seed SHA-256"], "f".repeat(64));
  assert.equal(rows.Rules, "r1");
  assert.equal(rows["Chain head"], "abc");
  assert.equal(rows.Journal, "j".repeat(64));
});

test("a seed that does not hash to its commitment is flagged; authored runs have no seed rows", () => {
  assert.match(facts(cardRows(base, {}, undefined, undefined, "0".repeat(64)))["Seed SHA-256"], /does NOT match/);
  const authored = facts(cardRows({ ...base, variant: "rally", seed_commitment: null, stressed_days: null, generated_days: null }, {}));
  assert.equal(authored.Variant, "rally");
  for (const k of ["Seed", "Seed SHA-256", "Stressed days", "Rules", "Chain head", "Mean Brier"]) assert.equal(authored[k], undefined);
});

test("mean Brier skips a seat without scored theses; a partial outcome never throws", () => {
  const research = { seats: { pm: { theses: 2, mean_brier: "0.25" }, mp: { theses: 0, mean_brier: null } } } as unknown as Debrief["research"];
  assert.equal(facts(cardRows(base, {}, research))["Mean Brier"], "PM 0.25 (2)");
  const bare = facts(cardRows({ label: "WIN", score: "12.5" } as Outcome, {}));
  assert.equal(bare.Result, "Score +12.5 bps");
  assert.equal(bare.Variant, "base");
  assert.equal(bare.Scenario, undefined);
});

test("money and the market line follow Godot; campaign runs never get Case 1's day 16 text", () => {
  assert.equal(exactMoney("-1234567.123"), "-$1,234,567.123");
  assert.equal(exactMoney("1"), "$1.00");
  assert.equal(marketText("base", "campaign-v1"), 'The campaign-v1 run\'s hidden variant was "base".');
  assert.match(marketText("base", "case1"), /^The day 16 market was a sell-off/);
  assert.equal(cardText({ ...base, label: "COMPANY_FAILURE", variant: "base", scenario: "campaign-v1" }, [["k", "v"]]),
    'FundForge: Company failure\nThe campaign-v1 run\'s hidden variant was "base".\nk: v\nFictional fund; no real money.');
});

test("the landing page offers exactly Godot's scenario menu", () => {
  const gd = readFileSync(new URL("../../game/scripts/world_rules.gd", import.meta.url), "utf8");
  const block = /const SCENARIOS := \[([\s\S]*?)\n\]/.exec(gd)![1];
  assert.deepEqual([...block.matchAll(/\["([^"]+)", "([^"]+)"\]/g)].map((m) => [m[1], m[2]]), SCENARIOS.map(([k, v]) => [k, v]));
});
