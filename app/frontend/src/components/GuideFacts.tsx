import { formatCommitDate } from "../commitDate";
import { useI18n } from "../i18n";
import { OK_SYMBOL, SEVERITY_SYMBOLS } from "../symbols";
import type { GuideInfo } from "../types";

const SHORT_COMMIT_LENGTH = 7;

function shortCommit(commit: string | null): string | null {
  return commit === null ? null : commit.slice(0, SHORT_COMMIT_LENGTH);
}

interface GuideFactsProps {
  guide: GuideInfo;
}

/** Stand des Guide-Klons (Branch, Commit, XSD, Prüfung, Teststand); Status-Box und Hilfeseite teilen sie. */
export function GuideFacts({ guide }: GuideFactsProps) {
  const { t, language } = useI18n();
  const unknown = t("guide.unknown");
  const testSymbol = guide.testState === "tested" ? OK_SYMBOL : SEVERITY_SYMBOLS.info;
  const xsdCommit = shortCommit(guide.xsdCommit);
  const commitDate =
    guide.commitDate === null ? null : formatCommitDate(guide.commitDate, language);
  return (
    <dl className="guide-facts">
      <dt>{t("guide.branch")}</dt>
      <dd>{guide.branch ?? unknown}</dd>
      <dt>{t("guide.commit")}</dt>
      <dd>
        <code title={guide.commit ?? undefined}>{shortCommit(guide.commit) ?? unknown}</code>
        {guide.commit !== null && (
          <>
            {", "}
            <span title={guide.commitDate ?? undefined}>
              {commitDate ?? t("guide.dateUnknown")}
            </span>
          </>
        )}
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
      {guide.xsdPresent && (
        <>
          <dt>{t("guide.validation")}</dt>
          <dd>
            {guide.examplesReady ? (
              <>
                <span aria-hidden="true">{OK_SYMBOL}</span> {t("guide.validationReady")}
              </>
            ) : (
              <>
                <span aria-hidden="true">{SEVERITY_SYMBOLS.info}</span>{" "}
                {t(guide.xsdLoaded ? "guide.examplesChecking" : "guide.xsdLoading")}
              </>
            )}
          </dd>
        </>
      )}
      <dt>{t("guide.test")}</dt>
      <dd>
        <span aria-hidden="true">{testSymbol}</span> {t(`guide.testState.${guide.testState}`)}
      </dd>
      <dt>{t("guide.mapping")}</dt>
      <dd>{t("guide.mappingSheets", { count: guide.mappingSheets.length })}</dd>
    </dl>
  );
}
