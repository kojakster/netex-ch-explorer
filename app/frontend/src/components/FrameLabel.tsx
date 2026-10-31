import { useI18n } from "../i18n";
import type { FrameColor } from "../types";

/** Beschriftung einer Farbe: NeTEx-Frame-Namen unverändert, sonst Text aus der Sprachdatei. */
export function useFrameLabel(): (key: string) => string {
  const { t } = useI18n();
  return (key) => (key.endsWith("Frame") ? key : t(`frame.${key}`));
}

interface FrameSwatchProps {
  color: FrameColor;
}

/** Farbiges Kästchen mit Frame-Name als Text (Farbe nie ohne Text). */
export function FrameSwatch({ color }: FrameSwatchProps) {
  const label = useFrameLabel();
  return (
    <span className="frame-swatch" style={{ backgroundColor: color.background, color: color.text }}>
      {label(color.key)}
    </span>
  );
}
