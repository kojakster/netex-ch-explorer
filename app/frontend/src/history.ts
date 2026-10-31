// Verlauf der besuchten Objekte und Angaben (vor/zurück), ohne Abhängigkeit von React.

export interface Selection {
  /** Das angezeigte Objekt. */
  objectId: string;
  /** Die markierte Angabe: das Objekt selbst oder eines seiner Elemente. */
  elementId: string;
}

export interface History {
  entries: readonly Selection[];
  index: number;
}

export const EMPTY_HISTORY: History = { entries: [], index: -1 };

export function currentSelection(history: History): Selection | null {
  return history.entries[history.index] ?? null;
}

export function canGoBack(history: History): boolean {
  return history.index > 0;
}

export function canGoForward(history: History): boolean {
  return history.index < history.entries.length - 1;
}

/** Besucht eine Auswahl; was vor- lag, entfällt. Dieselbe Auswahl zweimal ergibt einen Eintrag. */
export function visit(history: History, selection: Selection): History {
  const current = currentSelection(history);
  if (
    current !== null &&
    current.objectId === selection.objectId &&
    current.elementId === selection.elementId
  ) {
    return history;
  }
  const entries = [...history.entries.slice(0, history.index + 1), selection];
  return { entries, index: entries.length - 1 };
}

export function goBack(history: History): History {
  return canGoBack(history) ? { ...history, index: history.index - 1 } : history;
}

export function goForward(history: History): History {
  return canGoForward(history) ? { ...history, index: history.index + 1 } : history;
}
