import { defineConfig } from "@playwright/test";

// E2E-Test: startet den echten Server (`scripts/start.py`) auf einem eigenen Testport, damit ein
// laufender Explorer auf dem Standardport nicht stört. Der Server wird nach dem Lauf beendet.
const PORT = Number(process.env.E2E_PORT ?? "8766");
const BASE_URL = `http://127.0.0.1:${PORT}`;
// Standard: der von Playwright installierte Chromium (`npm run e2e:install`). Mit
// `E2E_BROWSER_CHANNEL=chrome` (oder `msedge`) wird der installierte Browser des Rechners benutzt.
const CHANNEL = process.env.E2E_BROWSER_CHANNEL;

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: "list",
  timeout: 60_000,
  use: {
    baseURL: BASE_URL,
    viewport: { width: 1700, height: 1100 },
    ...(CHANNEL === undefined || CHANNEL === "" ? {} : { channel: CHANNEL }),
  },
  webServer: {
    command: `uv run python scripts/start.py --no-browser --port ${PORT}`,
    cwd: "../..",
    url: `${BASE_URL}/api/guide`,
    // Beim ersten Lauf baut der Start die Oberfläche (npm ci, npm run build).
    timeout: 240_000,
    reuseExistingServer: false,
    gracefulShutdown: { signal: "SIGINT", timeout: 10_000 },
  },
});
