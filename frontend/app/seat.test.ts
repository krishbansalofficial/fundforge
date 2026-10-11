import assert from "node:assert/strict";
import { test } from "node:test";
import { seatTokenFromUrl } from "./seat.ts";

test("seat token comes from the fragment, falling back to the legacy query", () => {
  assert.equal(seatTokenFromUrl("#t=abc-_1", ""), "abc-_1");
  assert.equal(seatTokenFromUrl("#t=frag", "?t=query"), "frag");
  assert.equal(seatTokenFromUrl("", "?t=query"), "query");
  assert.equal(seatTokenFromUrl("", ""), null);
});
