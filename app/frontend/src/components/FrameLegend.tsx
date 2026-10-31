import { useI18n } from "../i18n";
import type { FrameColor } from "../types";
import { FrameSwatch } from "./FrameLabel";

interface FrameLegendProps {
  colors: readonly FrameColor[];
  onHelp: () => void;
}

/** Immer sichtbare Farblegende der Frames mit Verweis auf die Hilfeseite. */
export function FrameLegend({ colors, onHelp }: FrameLegendProps) {
  const { t } = useI18n();
  return (
    <section className="legend" aria-label={t("legend.title")}>
      <h2>{t("legend.title")}</h2>
      <ul>
        {colors.map((color) => (
          <li key={color.key}>
            <FrameSwatch color={color} />
          </li>
        ))}
      </ul>
      <button type="button" className="link-button" onClick={onHelp}>
        {t("legend.explain")}
      </button>
    </section>
  );
}
