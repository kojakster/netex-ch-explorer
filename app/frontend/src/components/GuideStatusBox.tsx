import { useI18n } from "../i18n";
import type { GuideInfo } from "../types";
import { GuideFacts } from "./GuideFacts";
import { IssueList } from "./IssueList";

interface GuideStatusBoxProps {
  guide: GuideInfo;
}

/** Guide-Status-Box links oben: Stand des Guide-Klons und Probleme mit Handlungshinweis. */
export function GuideStatusBox({ guide }: GuideStatusBoxProps) {
  const { t } = useI18n();
  return (
    <section className="guide-status" aria-label={t("guide.title")}>
      <h2>{t("guide.title")}</h2>
      <p className="guide-profile">
        {t("guide.profile")} <span className="badge">{t("guide.inDevelopment")}</span>
      </p>
      {guide.found && <GuideFacts guide={guide} />}
      <IssueList issues={guide.issues} />
    </section>
  );
}
