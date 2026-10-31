import { useI18n } from "../i18n";
import { SEVERITY_SYMBOLS } from "../symbols";
import type { Issue } from "../types";

/** Meldungen haben keine eigene Kennung; der Inhalt identifiziert sie eindeutig genug. */
function issueKey(issue: Issue): string {
  return `${issue.severity}|${issue.key}|${JSON.stringify(issue.params)}`;
}

interface IssueListProps {
  issues: readonly Issue[];
}

/** Meldungen mit Symbol und Text des Schweregrads (nie nur Farbe). */
export function IssueList({ issues }: IssueListProps) {
  const { t } = useI18n();
  if (issues.length === 0) {
    return null;
  }
  return (
    <ul className="issues">
      {issues.map((issue) => (
        <li key={issueKey(issue)} className={`issue issue-${issue.severity}`}>
          <span className="issue-severity">
            <span aria-hidden="true">{SEVERITY_SYMBOLS[issue.severity]}</span>{" "}
            {t(`severity.${issue.severity}`)}
          </span>{" "}
          <span className="issue-text">{t(issue.key, issue.params)}</span>
        </li>
      ))}
    </ul>
  );
}
