import { defineConfig } from "@playwright/test";

// The web desk and API must already be running (CI starts both; see .github/workflows/ci.yml).
export default defineConfig({
  testDir: "e2e",
  timeout: 180_000,
  retries: 0,
  reporter: [["list"]],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://127.0.0.1:3011",
    viewport: { width: 1400, height: 1000 },
    trace: "retain-on-failure",
    launchOptions: process.env.PW_CHROMIUM ? { executablePath: process.env.PW_CHROMIUM } : {},
  },
});
