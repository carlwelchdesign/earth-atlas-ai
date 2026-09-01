import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  timeout: 45_000,
  expect: { timeout: 30_000 },
  fullyParallel: false,
  reporter: "line",
  use: {
    baseURL:
      process.env.ECHOATLAS_PUBLIC_URL ?? "https://earth-atlas-ai.vercel.app",
    channel: "chrome",
    viewport: { width: 1440, height: 1000 },
  },
});
