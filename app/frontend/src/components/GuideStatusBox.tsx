import { useI18n } from "../i18n";
import { OK_SYMBOL, SEVERITY_SYMBOLS } from "../symbols";
import type { GuideInfo } from "../types";
import { IssueList } from "./IssueList";

const SHORT_COMMIT_LENGTH = 7;

function shortCommit(commit: string | null): string | null {
  return commit === null ? null : commit.slice(0, SHORT_COMMIT_LENGTH);
}

interface GuideStatusBoxProps {
  guide: GuideInfo;
}

/** Guide-Status-Box links oben: Stand des Guide-Klons und Probleme mit Handlungshinweis. */
export function GuideStatusBox({ guide }: GuideStatusBoxProps) {
  const { t } = useI18n();
  const unknown = t("guide.unknown");
  const testSymbol = guide.testState === "tested" ? OK_SYMBOL : SEVERITY_SYMBOLS.info;
  const xsdCommit = shortCommit(guide.xsdCommit);
  return (
    <section className="guide-status" aria-label={t("guide.title")}>
      <h2>{t("guide.title")}</h2>
      <p className="guide-profile">
        {t("guide.profile")} <span className="badge">{t("guide.inDevelopment")}</span>
      </p>
      {guide.found && (
        <dl>
          <dt>{t("guide.branch")}</dt>
          <dd>{guide.branch ?? unknown}</dd>
          <dt>{t("guide.commit")}</dt>
          <dd>
            <code title={guide.commit ?? undefined}>{shortCommit(guide.commit) ?? unknown}</code>
          </dd>
          <dt>{t("guide.xsd")}</dt>
          <dd>
            {guide.xsdPresent ? (
              <>
                <span aria-hidden="true">{OK_SYMBOL}</span> {t("guide.xsdPresent")}
                {xsdCommit !== null && (
                  <>
                    {" "}
                    <code title={guide.xsdCommit ?? undefined}>{xsdCommit}</code>
                  </>
                )}
              </>
            ) : (
              <>
                <span aria-hidden="true">{SEVERITY_SYMBOLS.error}</span> {t("guide.xsdMissing")}
              </>
            )}
          </dd>
          <dt>{t("guide.test")}</dt>
          <dd>
            <span aria-hidden="true">{testSymbol}</span> {t(`guide.testState.${guide.testState}`)}
          </dd>
          <dt>{t("guide.mapping")}</dt>
          <dd>{t("guide.mappingSheets", { count: guide.mappingSheets.length })}</dd>
        </dl>
      )}
      <IssueList issues={guide.issues} />
    </section>
  );
}
