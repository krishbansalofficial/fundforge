import assert from "node:assert/strict";
import { test } from "node:test";
import { admissionAmounts, packageTerms } from "./prospect.ts";

test("admission choices are the cap-step multiples up to escrow, largest first", () => {
  assert.deepEqual(admissionAmounts("5000000", "1000000"), ["5000000", "4000000", "3000000", "2000000", "1000000"]);
  assert.deepEqual(admissionAmounts("2500000", "1000000"), ["2000000", "1000000"]);
  assert.deepEqual(admissionAmounts("0", "1000000"), []);
  for (const [escrow, step] of [["5000000", null], ["5000000", "0"], ["5000000.5", "1000000"], ["5000000", "abc"]] as const)
    assert.deepEqual(admissionAmounts(escrow, step), [], `${escrow} / ${step}`);
});

test("package terms describe winddown and admission and leave other kinds alone", () => {
  assert.match(packageTerms("winddown", { day: 3 })!, /day 3.*every unit is redeemed/);
  assert.equal(packageTerms("admission", { series: "Anchor", amount: "3000000", deal_day: 20, issue_price: "100", hwm: "100" }),
    "Admit Anchor for $3,000,000 at the day 20 dealing close, issue price 100, high-water mark 100, subject to certification and post-flow checks.");
  assert.equal(packageTerms("gate", {}), null);
});
