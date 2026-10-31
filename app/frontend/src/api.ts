// Austauschbare Datenschicht: lokal über HTTP, später in der Webversion direkt über Pyodide.

import type {
  AppInfo,
  ChainLink,
  DatasetInfo,
  DiagnosticInfo,
  GuideInfo,
  JourneyInfo,
  JourneyViewInfo,
  ObjectDetail,
  ObjectSearchResult,
  SearchParams,
  XmlWindow,
} from "./types";

export interface DataSource {
  getAppInfo(): Promise<AppInfo>;
  getGuide(): Promise<GuideInfo>;
  openExample(name: string): Promise<DatasetInfo>;
  getJourneys(datasetId: string): Promise<JourneyInfo[]>;
  getJourney(journeyId: string): Promise<JourneyViewInfo>;
  searchObjects(datasetId: string, params: SearchParams): Promise<ObjectSearchResult>;
  getDiagnostics(datasetId: string): Promise<DiagnosticInfo[]>;
  getObject(objectId: string): Promise<ObjectDetail>;
  getObjectXml(objectId: string): Promise<XmlWindow>;
  getProvenance(objectId: string): Promise<ChainLink[]>;
  getXmlAt(datasetId: string, file: number, line: number, column: number): Promise<XmlWindow>;
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

async function requestJson<T>(
  fetcher: typeof fetch,
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const response = await fetcher(path, {
    ...init,
    headers: { Accept: "application/json", "Content-Type": "application/json" },
  });
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

const enc = encodeURIComponent;

/** Datenquelle über die lokale HTTP-Schnittstelle (relative Pfade, gleicher Ursprung). */
export class HttpDataSource implements DataSource {
  private readonly fetcher: typeof fetch;

  constructor(fetcher: typeof fetch = (input, init) => fetch(input, init)) {
    this.fetcher = fetcher;
  }

  getAppInfo(): Promise<AppInfo> {
    return requestJson<AppInfo>(this.fetcher, "api/app");
  }

  getGuide(): Promise<GuideInfo> {
    return requestJson<GuideInfo>(this.fetcher, "api/guide");
  }

  openExample(name: string): Promise<DatasetInfo> {
    return requestJson<DatasetInfo>(this.fetcher, "api/datasets", {
      method: "POST",
      body: JSON.stringify({ example: name }),
    });
  }

  getJourneys(datasetId: string): Promise<JourneyInfo[]> {
    return requestJson<JourneyInfo[]>(this.fetcher, `api/datasets/${enc(datasetId)}/journeys`);
  }

  getJourney(journeyId: string): Promise<JourneyViewInfo> {
    return requestJson<JourneyViewInfo>(this.fetcher, `api/journeys/${enc(journeyId)}`);
  }

  searchObjects(datasetId: string, params: SearchParams): Promise<ObjectSearchResult> {
    const query = new URLSearchParams({
      limit: String(params.limit),
      offset: String(params.offset),
    });
    if (params.type) {
      query.set("type", params.type);
    }
    if (params.q) {
      query.set("q", params.q);
    }
    return requestJson<ObjectSearchResult>(
      this.fetcher,
      `api/datasets/${enc(datasetId)}/objects?${query.toString()}`,
    );
  }

  getDiagnostics(datasetId: string): Promise<DiagnosticInfo[]> {
    return requestJson<DiagnosticInfo[]>(
      this.fetcher,
      `api/datasets/${enc(datasetId)}/diagnostics`,
    );
  }

  getObject(objectId: string): Promise<ObjectDetail> {
    return requestJson<ObjectDetail>(this.fetcher, `api/objects/${enc(objectId)}`);
  }

  getObjectXml(objectId: string): Promise<XmlWindow> {
    return requestJson<XmlWindow>(this.fetcher, `api/objects/${enc(objectId)}/xml`);
  }

  getProvenance(objectId: string): Promise<ChainLink[]> {
    return requestJson<ChainLink[]>(this.fetcher, `api/objects/${enc(objectId)}/provenance`);
  }

  getXmlAt(datasetId: string, file: number, line: number, column: number): Promise<XmlWindow> {
    const query = new URLSearchParams({
      file: String(file),
      line: String(line),
      column: String(column),
    });
    return requestJson<XmlWindow>(
      this.fetcher,
      `api/datasets/${enc(datasetId)}/xml?${query.toString()}`,
    );
  }
}
