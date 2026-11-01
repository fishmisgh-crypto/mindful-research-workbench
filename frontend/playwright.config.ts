import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1, // this machine has ~8 GB RAM; parallel Chromium workers crashed under memory pressure
  reporter: "list",
  use: { baseURL: "http://localhost:3000", contextOptions: { reducedMotion: "reduce" } }, // stable screenshots
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    command: "npm run start -- --hostname 127.0.0.1 --port 3000",
    url: "http://localhost:3000",
    reuseExistingServer: true,
    timeout: 120_000,
  },
});
