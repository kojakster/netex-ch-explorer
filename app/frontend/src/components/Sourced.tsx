import type { ReactNode } from "react";
import { colorOf } from "../colors";
import { useI18n } from "../i18n";
import type { FrameColor, ObjectInfo, ValueInfo } from "../types";

interface SourcedProps {
  /** Quelle der Angabe; ohne Quelle erscheint der Inhalt als einfacher Text. */
  element: ObjectInfo | null;
  colors: readonly FrameColor[];
  selected: string | null;
  onSelect: (elementId: string) => void;
  className?: string | undefined;
  children: ReactNode;
}

/**
 * Angabe mit Herkunft: trägt die Farbe des Frames am linken Rand; ein Klick wählt die Stelle
 * im XML und zeigt die Herkunftskette. Der Frame steht im Tooltip und im Namen für Screenreader.
 */
export function Sourced({
  element,
  colors,
  selected,
  onSelect,
  className = "",
  children,
}: SourcedProps) {
  const { t } = useI18n();
  if (element === null) {
    return <span className={className}>{children}</span>;
  }
  const color = colorOf(element, colors);
  const style = color === null ? undefined : { borderLeftColor: color.background };
  const title = t("sourced.title", {
    element: element.name,
    frame: element.frame?.name ?? "",
    line: element.line,
    column: element.column,
  });
  return (
    <button
      type="button"
      className={`sourced ${className}${selected === element.id ? " selected" : ""}`}
      style={style}
      title={title}
      onClick={() => onSelect(element.id)}
    >
      {children}
    </button>
  );
}

interface ValueTextProps {
  value: ValueInfo;
  colors: readonly FrameColor[];
  selected: string | null;
  onSelect: (elementId: string) => void;
  className?: string | undefined;
}

/** Angabe aus der Datei oder der Grund, warum sie fehlt (nie ein Ersatzwert). */
export function ValueText({ value, colors, selected, onSelect, className }: ValueTextProps) {
  const { t } = useI18n();
  const content =
    value.status === "found" ? (
      value.text
    ) : (
      <span className="lookup-missing">
        {t(`lookup.${value.status}`, { ref: value.text ?? "" })}
      </span>
    );
  return (
    <Sourced
      element={value.element}
      colors={colors}
      selected={selected}
      onSelect={onSelect}
      className={className}
    >
      {content}
    </Sourced>
  );
}
