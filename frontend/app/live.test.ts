import assert from "node:assert/strict";
import { test } from "node:test";
import { backoff, socketUrl } from "./live.ts";

test("socket URL follows the page origin unless an API origin is configured", () => {
  assert.equal(socketUrl("ab12", "https://arena.example"), "wss://arena.example/api/rooms/ab12/presence");
  assert.equal(socketUrl("ab12", "http://127.0.0.1:3011", ""), "ws://127.0.0.1:3011/api/rooms/ab12/presence");
  assert.equal(socketUrl("ab12", "https://web.example", "https://api.example/"), "wss://api.example/api/rooms/ab12/presence");
});

test("backoff doubles from 1 s, caps at 30 s, and adds at most 30% jitter", () => {
  assert.deepEqual([0, 1, 2, 3, 4, 5, 9].map((a) => backoff(a, () => 0)), [1000, 2000, 4000, 8000, 16000, 30000, 30000]);
  assert.equal(backoff(9, () => 1), 39000);
});
