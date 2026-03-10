import path from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig, devices } from "@playwright/test";

function shellQuote(value: string): string {
  return `'${value.replace(/'/g, `'\"'\"'`)}'`;
}

const frontendDir = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(frontendDir, "..", "..");
const outputDir = path.join(repoRoot, "output", "playwright");
const databasePath = path.join(outputDir, "news-perspective-e2e.db");
const backendActivate = path.join(
  repoRoot,
  "src",
  "backend",
  ".venv",
  "bin",
  "activate"
);
const databaseUrl = `sqlite:///${databasePath}`;

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  outputDir: path.join(outputDir, "test-results"),
  reporter: [["list"]],
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  use: {
    baseURL: "http://127.0.0.1:3000",
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
    video: "retain-on-failure",
  },
  webServer: [
    {
      command: `zsh -lc "mkdir -p ${shellQuote(outputDir)} && rm -f ${shellQuote(databasePath)} && source ${shellQuote(backendActivate)} && export DATABASE_URL=${shellQuote(databaseUrl)} && python -m src.backend.scripts.seed_manual_integration_data && uvicorn src.backend.main:app --host 127.0.0.1 --port 8000"`,
      cwd: repoRoot,
      timeout: 120_000,
      url: "http://127.0.0.1:8000/api/stats",
      reuseExistingServer: false,
    },
    {
      command: "npm run dev -- --hostname 127.0.0.1 --port 3000",
      cwd: frontendDir,
      timeout: 120_000,
      url: "http://127.0.0.1:3000",
      reuseExistingServer: false,
    },
  ],
  projects: [
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
      },
    },
  ],
});
