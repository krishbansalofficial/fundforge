import assert from "node:assert/strict";
import { test } from "node:test";
import type { components } from "./api-types";
import { mergePage, olderCursor, type Journal } from "./journal.ts";

type LedgerPage = components["schemas"]["LedgerPage"];
const entry = (n: number) => ({ id: `e${n}`, entity: "fund", date: "2026-01-02", memo: `m${n}`, postings: [] });
/** What the server returns for entries [from, to) of the journal. */
const page = (from: number, to: number, digest = `d${to}`): LedgerPage =>
  ({ entity: "fund", entries: Array.from({ length: to - from }, (_, i) => entry(from + i)), next: to, digest });
const ids = (j: Journal) => j.entries.map((e) => e.id);

test("newest page first, then older pages prepend and the cursor runs to zero", () => {
  let j = mergePage(null, page(1500, 2500));
  assert.equal(olderCursor(j), 500);
  j = mergePage(j, page(500, 1500, "old"));
  assert.equal(j.digest, "d2500");
  assert.equal(olderCursor(j), 0);
  // The server returns [0, 1000) for after=0; the overlap with [500, ...) is kept once.
  j = mergePage(j, page(0, 1000));
  assert.deepEqual([j.start, j.next, j.entries.length], [0, 2500, 2500]);
  assert.deepEqual(ids(j), Array.from({ length: 2500 }, (_, n) => `e${n}`));
  assert.equal(olderCursor(j), null);
});

test("the room advancing between pages adds new entries without duplicates", () => {
  let j = mergePage(null, page(10, 20));
  j = mergePage(j, page(20, 23));          // after=next once the room advanced
  j = mergePage(j, page(15, 25));          // a fresh newest page overlapping what is loaded
  j = mergePage(j, page(0, 10));           // an older page fetched after the room advanced
  assert.deepEqual(ids(j), Array.from({ length: 25 }, (_, n) => `e${n}`));
  assert.equal(j.digest, "d25");
  assert.deepEqual(ids(mergePage(j, page(25, 25))), ids(j)); // an empty refresh changes nothing
});

test("a gap or a rewritten overlap is refused rather than spliced", () => {
  const j = mergePage(null, page(10, 20));
  assert.throws(() => mergePage(j, page(21, 30)), /not contiguous/);
  assert.throws(() => mergePage(j, page(0, 9)), /not contiguous/);
  const other = { ...page(15, 25), entries: page(15, 25).entries.map((e) => ({ ...e, id: `x${e.id}` })) };
  assert.throws(() => mergePage(j, other), /changed/);
});
