import assert from "node:assert/strict";
import { test } from "node:test";
import { complement, num } from "./lib.ts";

test("complement is exact and refuses anything outside 0..1 or past 6 decimals", () => {
  assert.equal(complement("0.3"), "0.7");
  assert.equal(complement("0.000001"), "0.999999");
  assert.equal(complement("1"), "0");
  assert.equal(complement("0"), "1");
  assert.equal(complement("1.000000"), "0");
  for (const bad of ["1.1", "1.000001", "-0.1", "0.1234567", ".5", "", "abc", "2"]) assert.equal(complement(bad), null, bad);
});

test("counts use a fixed en-US grouping", () => {
  assert.equal(num(100000), "100,000");
});
