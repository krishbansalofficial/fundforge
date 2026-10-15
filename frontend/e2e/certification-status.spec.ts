import { expect, test } from "@playwright/test";

test("NAV distinguishes latest dealing-close certification from intraday marks", async ({ page, request }) => {
  const created = await request.post("/api/rooms", { data: { pm_name: "Cert PM", mp_name: "Cert MP" } });
  expect(created.status()).toBe(201);
  const { room_id: room, tokens } = await created.json();
  const snapshot = await (await request.get(`/api/rooms/${room}/view`, { headers: { Authorization: `Bearer ${tokens.pm}` } })).json();
  let status: string | null = null;
  await page.route(`**/api/rooms/${room}/view`, route => route.fulfill({ json: { ...snapshot, certification: status } }));
  await page.goto(`/room/${room}#t=${tokens.pm}`);
  const nav = page.getByRole("region", { name: "Fund status" }).locator(".figure").first();
  await expect(nav).toContainText("Latest dealing-close: Pending");
  await expect(nav).toContainText("No dealing-close certificate yet.");
  await expect(nav).toContainText("Status applies to the latest dealing close, not a new check of current NAV.");
  status = "certified";
  await expect(nav).toContainText("Latest dealing-close: Certified");
  await expect(nav).not.toContainText("No dealing-close certificate yet.");
  status = "broken";
  await expect(nav).toContainText("Latest dealing-close: Broken");
  await expect(nav).toContainText("Latest dealing was withheld; inspect RISK certification.");
  await expect(nav).toContainText("Status applies to the latest dealing close, not a new check of current NAV.");
  status = "pending";
  await expect(nav).toContainText("Latest dealing-close: Pending");
  await expect(nav).not.toContainText("was withheld");
});
