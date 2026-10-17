import assert from "node:assert/strict";
import { test } from "node:test";
import { cardRows, cardText } from "./card.ts";
import type { Outcome } from "./lib.ts";

const base = {
  label: "WIN", nav: "25012345.6", rank: 2, funds: 5, score: "12.5", fund_return_bps: "48.1", benchmark_return_bps: "-35.6",
  excess_bps: "83.7", max_drawdown: "0.0123", scenario: "case1-generated", variant: "seed:abc", seed_commitment: "f".repeat(64),
  journal_digest: "j".repeat(64), tape_digest: "t", forced: [], unpaid: [], recall_resolved_by: null, redemption_paid: "0",
} as Outcome;

test("card rows are server fields, formatted only, and flag a seed that does not match its commitment", () => {
  const rows = Object.fromEntries(cardRows(base, { pm: "Ana", mp: "Ben" }, "2026.10.8", "f".repeat(64)));
  assert.equal(rows["vs benchmark"], "fund +48.1 bps vs passive book -35.6 bps (excess +83.7 bps)");
  assert.equal(rows["Final NAV"], "$25,012,345.60");
  assert.equal(rows["Max drawdown"], "1.23% (NAV per unit, at closes)");
  assert.equal(rows.Seed, "abc");
  assert.equal(rows["Seed SHA-256"], "f".repeat(64));
  assert.equal(rows.Rules, "2026.10.8");
  assert.match(Object.fromEntries(cardRows(base, {}, "r", "0".repeat(64)))["Seed SHA-256"], /does NOT match/);
  const authored = Object.fromEntries(cardRows({ ...base, variant: "base", seed_commitment: null }, {}, "r"));
  assert.equal(authored.Variant, "base");
  assert.equal(authored.Seed, undefined);
  assert.match(cardText(base, cardRows(base, {}, "r")), /^FundForge: Win\n/);
});
