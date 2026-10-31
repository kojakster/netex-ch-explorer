import type { FrameColor } from "../types";

/** Gemeinsame Eigenschaften aller Bausteine der Fahrtansicht, die Angaben mit Herkunft zeigen. */
export interface SourceProps {
  colors: readonly FrameColor[];
  /** Die gewählte Angabe (Element-ID) oder `null`. */
  selected: string | null;
  onSelect: (elementId: string) => void;
}
