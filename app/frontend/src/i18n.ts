// Kleine eigene Übersetzungsfunktion: flache Schlüssel, Platzhalter {name}.

import { createContext, useContext } from "react";
import deCH from "./locales/de-CH.json";
import en from "./locales/en.json";

export type Messages = Readonly<Record<string, string>>;
export type Params = Readonly<Record<string, string | number>>;

export const MESSAGES: Readonly<Record<string, Messages>> = { "de-CH": deCH, en };
export const DEFAULT_LANGUAGE = "de-CH";

/** Endung des Schlüssels mit dem Text für die Einzahl (`count` ist genau 1). */
export const SINGULAR_SUFFIX = ".one";

/**
 * Setzt die Parameter in den Text des Schlüssels ein; fehlt der Schlüssel, erscheint er selbst.
 * Ist der Parameter `count` genau 1 und gibt es `<Schlüssel>.one`, gilt dieser Text (Einzahl).
 */
export function translate(messages: Messages, key: string, params: Params = {}): string {
  const singular = String(params.count) === "1" ? messages[`${key}${SINGULAR_SUFFIX}`] : undefined;
  const template = singular ?? messages[key];
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
