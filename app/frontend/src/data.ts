// Zugriff der Komponenten auf die Datenquelle und Laden mit Fehlerschlüssel.

import { createContext, useContext, useEffect, useRef, useState } from "react";
import { ApiError, type DataSource } from "./api";

export const DataSourceContext = createContext<DataSource | null>(null);

export function useDataSource(): DataSource {
  const source = useContext(DataSourceContext);
  if (source === null) {
    throw new Error("DataSourceContext fehlt");
  }
  return source;
}

export const LOAD_ERROR_KEY = "app.loadError";

export interface Loaded<T> {
  data: T | null;
  errorKey: string | null;
  loading: boolean;
}

/**
 * Lädt Daten neu, sobald sich `requestKey` ändert (`null` = nichts laden).
 * Mit dem Schlüsselwechsel verschwinden die alten Daten (`data` ist `null`, `loading` ist `true`),
 * damit nichts zum alten Schlüssel angezeigt oder angeklickt wird. Ältere Antworten werden verworfen.
 */
export function useLoad<T>(requestKey: string | null, load: () => Promise<T>): Loaded<T> {
  const [state, setState] = useState<Loaded<T>>({ data: null, errorKey: null, loading: false });
  const loadRef = useRef(load);
  loadRef.current = load;
  useEffect(() => {
    if (requestKey === null) {
      setState({ data: null, errorKey: null, loading: false });
      return;
    }
    let active = true;
    setState({ data: null, errorKey: null, loading: true });
    loadRef
      .current()
      .then((data) => {
        if (active) {
          setState({ data, errorKey: null, loading: false });
        }
      })
      .catch((error: unknown) => {
        if (active) {
          const errorKey = error instanceof ApiError ? error.key : LOAD_ERROR_KEY;
          setState({ data: null, errorKey, loading: false });
        }
      });
    return () => {
      active = false;
    };
  }, [requestKey]);
  return state;
}
