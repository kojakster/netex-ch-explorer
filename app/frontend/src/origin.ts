// Schalter „Herkunft zeigen“: Ein Kontext statt einer Eigenschaft in jedem Baustein der Fahrtansicht.

import { createContext, useContext } from "react";

/** `true`: Frame-Farbbalken, NeTEx-Namen und Zusatzzeilen sind sichtbar (Standard für andere Ansichten). */
export const OriginContext = createContext(true);

export function useShowOrigin(): boolean {
  return useContext(OriginContext);
}
