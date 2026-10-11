import assert from "node:assert/strict";
import { test } from "node:test";
import { exclusive } from "./exclusive.ts";

test("a second submission while the first is in flight is dropped, then allowed again", async () => {
  const flag = { current: false };
  const sent: number[] = [];
  let release!: () => void;
  const first = exclusive(flag, () => new Promise<void>((r) => { sent.push(1); release = r; }));
  assert.equal(await exclusive(flag, async () => { sent.push(2); }), false);
  release();
  assert.equal(await first, true);
  assert.equal(await exclusive(flag, async () => { sent.push(3); }), true);
  assert.deepEqual(sent, [1, 3]);
});

test("the flag is released when the request fails", async () => {
  const flag = { current: false };
  await assert.rejects(exclusive(flag, async () => { throw new Error("409"); }));
  assert.equal(flag.current, false);
});
