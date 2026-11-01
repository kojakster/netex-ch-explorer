import { useId, useState } from "react";
import { useI18n } from "../i18n";
import type { GuideInfo, Issue } from "../types";
import { GuideFacts } from "./GuideFacts";
import { IssueList } from "./IssueList";

export type GuideLevel = "ok" | "deviation" | "error";

interface GuideStatusBoxProps {
  guide: GuideInfo;
  /** Probleme der Einstellungsdateien; sie erscheinen in den Details und zählen für den Punkt. */
  settingsIssues?: readonly Issue[];
}

/**
 * Gesamtstand für den Punkt in der Kopfzeile: Fehler, wenn der Guide oder die XSD fehlt oder
 * eine Meldung ein Fehler ist; Abweichung bei anderem Teststand oder weiteren Meldungen.
 */
export function guideLevel(guide: GuideInfo, settingsIssues: readonly Issue[]): GuideLevel {
  const issues = [...guide.issues, ...settingsIssues];
  if (!guide.found || !guide.xsdPresent || issues.some((issue) => issue.severity === "error")) {
    return "error";
  }
  return guide.testState !== "tested" || issues.length > 0 ? "deviation" : "ok";
}

/** Guide-Status in der Kopfzeile: Punkt mit Kurztext; die Angaben klappen per Klick auf. */
export function GuideStatusBox({ guide, settingsIssues = [] }: GuideStatusBoxProps) {
  const { t } = useI18n();
  const panelId = useId();
  const [open, setOpen] = useState(false);
  const level = guideLevel(guide, settingsIssues);
  return (
    <div className="guide-status">
      <button
        type="button"
        className="status-button"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen(!open)}
      >
        <span className={`status-dot status-${level}`} aria-hidden="true" />
        {t(`guide.level.${level}`)}
      </button>
      {open && (
        <section id={panelId} className="guide-panel" aria-label={t("guide.title")}>
          <h2>{t("guide.title")}</h2>
          <p className="guide-profile">
            {t("guide.profile")} <span className="badge">{t("guide.inDevelopment")}</span>
          </p>
          {guide.found && <GuideFacts guide={guide} />}
          <IssueList issues={guide.issues} />
          {settingsIssues.length > 0 && (
            <>
              <h3>{t("settings.title")}</h3>
              <IssueList issues={settingsIssues} />
            </>
          )}
        </section>
      )}
    </div>
  );
}
