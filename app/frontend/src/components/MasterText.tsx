import { shortCommit } from "../format";
import { useI18n } from "../i18n";
import type { MasterInfo } from "../types";

interface MasterTextProps {
  master: MasterInfo | null;
  guideCommit: string | null;
  /** Kurzfassung für Tabellenzellen: nur die ersten zwei Werte je Zeile. */
  compact?: boolean;
}

/** Bedeutung eines Codes aus den Stammdaten, mit Blatt, Zeile und Guide-Stand. */
export function MasterText({ master, guideCommit, compact = false }: MasterTextProps) {
  const { t } = useI18n();
  if (master === null) {
    return null;
  }
  if (master.status === "unavailable") {
    return <span className="master master-none">{t("master.unavailable")}</span>;
  }
  if (master.status === "none") {
    return <span className="master master-none">{t("master.none")}</span>;
  }
  return (
    <span className="master">
      {master.matches.map((match) => {
        const source = t("master.source", {
          sheet: match.sheet,
          row: match.row,
          commit: shortCommit(guideCommit),
        });
        const summary = match.texts
          .slice(0, 2)
          .map((text) => text.text)
          .join(" \u00b7 ");
        if (compact) {
          return (
            <span key={`${match.sheet}|${match.row}`} className="master-match" title={source}>
              {summary}
            </span>
          );
        }
        return (
          <details key={`${match.sheet}|${match.row}`} className="master-match master-details">
            <summary>{summary}</summary>
            {match.texts.map((text) => (
              <span key={text.label} className="master-text">
                <span className="master-label">{text.label}</span> {text.text}
              </span>
            ))}
            <span className="master-source">{source}</span>
          </details>
        );
      })}
    </span>
  );
}
