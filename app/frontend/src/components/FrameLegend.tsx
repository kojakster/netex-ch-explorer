import { useI18n } from "../i18n";
import type { FrameColor } from "../types";
import { FrameSwatch } from "./FrameLabel";
import { ExcelIcon } from "./MasterText";

interface FrameLegendProps {
  colors: readonly FrameColor[];
  /** Mit Verweis auf die Hilfeseite, wenn angegeben. */
  onHelp?: (() => void) | undefined;
}

/** Kleine Farblegende der Frames; sie steht dort, wo Frame-Farben sichtbar sind. */
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
      <p className="legend-source">
        <ExcelIcon title={t("legend.mapping")} /> {t("legend.mapping")}
      </p>
      {onHelp !== undefined && (
        <button type="button" className="link-button" onClick={onHelp}>
          {t("legend.explain")}
        </button>
      )}
    </section>
  );
}
