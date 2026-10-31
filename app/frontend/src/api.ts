// Austauschbare Datenschicht: lokal über HTTP, später in der Webversion direkt über Pyodide.

import type { AppInfo, GuideInfo } from "./types";

export interface DataSource {
  getAppInfo(): Promise<AppInfo>;
  getGuide(): Promise<GuideInfo>;
}

/** Fehler der Schnittstelle mit Übersetzungsschlüssel aus dem einheitlichen Fehlerformat. */
export class ApiError extends Error {
  readonly key: string;

  constructor(key: string) {
    super(key);
    this.name = "ApiError";
    this.key = key;
  }
}

const FALLBACK_ERROR_KEY = "error.http";

function errorKey(body: unknown): string {
  if (typeof body === "object" && body !== null && "error" in body) {
    const error = (body as { error: unknown }).error;
    if (typeof error === "object" && error !== null && "key" in error) {
      const key = (error as { key: unknown }).key;
      if (typeof key === "string") {
        return key;
      }
    }
  }
  return FALLBACK_ERROR_KEY;
}

async function getJson<T>(fetcher: typeof fetch, path: string): Promise<T> {
  const response = await fetcher(path, { headers: { Accept: "application/json" } });
  if (!response.ok) {
    let body: unknown = null;
    try {
      body = await response.json();
    } catch {
      // Antwort ohne JSON-Inhalt: allgemeiner Fehlerschlüssel.
    }
    throw new ApiError(errorKey(body));
  }
  return (await response.json()) as T;
}

/** Datenquelle über die lokale HTTP-Schnittstelle (relative Pfade, gleicher Ursprung). */
export class HttpDataSource implements DataSource {
  private readonly fetcher: typeof fetch;

  constructor(fetcher: typeof fetch = (input, init) => fetch(input, init)) {
    this.fetcher = fetcher;
  }

  getAppInfo(): Promise<AppInfo> {
    return getJson<AppInfo>(this.fetcher, "api/app");
  }

  getGuide(): Promise<GuideInfo> {
    return getJson<GuideInfo>(this.fetcher, "api/guide");
  }
}
