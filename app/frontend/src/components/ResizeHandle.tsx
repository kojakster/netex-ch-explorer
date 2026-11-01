import type { KeyboardEvent, PointerEvent } from "react";
import { useRef } from "react";
import { clampWidth, widthAfterKey } from "../columnResize";
import { useI18n } from "../i18n";

interface ResizeHandleProps {
  /** Übersetzungsschlüssel der Beschriftung, z. B. „Breite der Navigation“. */
  labelKey: string;
  /** Aktuelle Breite der verstellbaren Spalte in Pixeln. */
  width: number;
  min: number;
  max: number;
  /** `true`: die Spalte liegt links vom Griff (Ziehen nach rechts verbreitert sie). */
  columnOnLeft: boolean;
  onChange: (width: number) => void;
  onReset: () => void;
}

/**
 * Griff zwischen zwei Spalten: mit Maus oder Finger ziehbar (Pointer Events), mit Pfeiltasten
 * verstellbar (Pos1/Ende: kleinste/grösste Breite), Doppelklick setzt die Standardbreite.
 */
export function ResizeHandle({
  labelKey,
  width,
  min,
  max,
  columnOnLeft,
  onChange,
  onReset,
}: ResizeHandleProps) {
  const { t } = useI18n();
  const drag = useRef<{ startX: number; startWidth: number } | null>(null);

  const onPointerDown = (event: PointerEvent<HTMLDivElement>) => {
    if (event.button !== 0) {
      return;
    }
    drag.current = { startX: event.clientX, startWidth: width };
    event.currentTarget.setPointerCapture?.(event.pointerId);
    event.preventDefault();
  };
  const onPointerMove = (event: PointerEvent<HTMLDivElement>) => {
    if (drag.current === null) {
      return;
    }
    const delta = event.clientX - drag.current.startX;
    const next = drag.current.startWidth + (columnOnLeft ? delta : -delta);
    onChange(clampWidth(next, min, max));
  };
  const endDrag = (event: PointerEvent<HTMLDivElement>) => {
    drag.current = null;
    if (event.currentTarget.hasPointerCapture?.(event.pointerId)) {
      event.currentTarget.releasePointerCapture(event.pointerId);
    }
  };
  const onKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    const next = widthAfterKey(event.key, event.shiftKey, width, min, max, columnOnLeft);
    if (next !== null) {
      event.preventDefault();
      onChange(next);
    }
  };

  return (
    // biome-ignore lint/a11y/useSemanticElements: Ein <hr> nimmt keinen Fokus an; das ARIA-Muster „Window Splitter“ verlangt einen fokussierbaren Trenner (role="separator" mit tabindex). Eintrag in docs/decisions.md.
    <div
      className="resize-handle"
      role="separator"
      aria-orientation="vertical"
      aria-label={t(labelKey)}
      aria-valuenow={width}
      aria-valuemin={min}
      aria-valuemax={max}
      tabIndex={0}
      title={t("resize.hint")}
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={endDrag}
      onPointerCancel={endDrag}
      onKeyDown={onKeyDown}
      onDoubleClick={onReset}
    />
  );
}
