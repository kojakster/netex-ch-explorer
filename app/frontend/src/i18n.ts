// Kleine eigene Übersetzungsfunktion: flache Schlüssel, Platzhalter {name}.

import { createContext, useContext } from "react";
import deCH from "./locales/de-CH.json";
import en from "./locales/en.json";

export type Messages = Readonly<Record<string, string>>;
export type Params = Readonly<Record<string, string | number>>;

export const MESSAGES: Readonly<Record<string, Messages>> = { "de-CH": deCH, en };
export const DEFAULT_LANGUAGE = "de-CH";

/** Setzt die Parameter in den Text des Schlüssels ein; fehlt der Schlüssel, erscheint er selbst. */
export function translate(messages: Messages, key: string, params: Params = {}): string {
  const template = messages[key];
  if (template === undefined) {
    return key;
  }
  return template.replace(/\{(\w+)\}/g, (placeholder, name: string) => {
    const value = params[name];
    return value === undefined ? placeholder : String(value);
  });
}

export function messagesFor(language: string): Messages {
  return MESSAGES[language] ?? deCH;
}

export type Translate = (key: string, params?: Params) => string;

export interface I18n {
  language: string;
  t: Translate;
}

export const I18nContext = createContext<I18n>({
  language: DEFAULT_LANGUAGE,
  t: (key, params) => translate(deCH, key, params),
});

export function useI18n(): I18n {
  return useContext(I18nContext);
}
