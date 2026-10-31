/// <reference types="vitest/config" />
import { readFileSync } from "node:fs";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const DEFAULT_PORT = 8765;

/** Port des lokalen Servers aus config/settings.json (eine Quelle für Server und Entwicklungsmodus). */
function serverPort(): number {
  try {
    const settings: unknown = JSON.parse(
      readFileSync(new URL("../../config/settings.json", import.meta.url), "utf-8"),
    );
    if (typeof settings === "object" && settings !== null && "port" in settings) {
      const port = (settings as { port: unknown }).port;
      if (typeof port === "number" && Number.isInteger(port)) {
        return port;
      }
    }
  } catch {
    // Fehlende oder ungültige Datei: wie der Server den Standardwert verwenden.
  }
  return DEFAULT_PORT;
}

export default defineConfig({
  plugins: [react()],
  // Relative Pfade, damit der Build auch als statische Webversion unter jedem Unterpfad läuft.
  base: "./",
  server: {
    host: "127.0.0.1",
    proxy: { "/api": `http://127.0.0.1:${serverPort()}` },
  },
  build: { sourcemap: false },
  test: {
    environment: "jsdom",
    globals: true,
  },
});
