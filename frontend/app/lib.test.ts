import assert from "node:assert/strict";
import { test } from "node:test";
import { complement, exactPct, num } from "./lib.ts";

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

test("exactPct moves the decimal point without float rounding", () => {
  assert.equal(exactPct("0.123456"), "12.3456");
  assert.equal(exactPct("0.000001"), "0.0001");
  assert.equal(exactPct("0.1"), "10");
  assert.equal(exactPct("1"), "100");
  assert.equal(exactPct("0.070000"), "7.0000");
  assert.equal(exactPct("0.29"), "29"); // 0.29 * 100 is 28.999999999999996 in floats
  assert.equal(exactPct("-0.0005"), "-0.05");
  assert.equal(exactPct("-0"), "0");
  for (const bad of ["", "abc", "1e-3", ".5", "0.1.2"]) assert.equal(exactPct(bad), null, bad);
});
