import { useDataSource, useLoad } from "../data";
import { useI18n } from "../i18n";
import { OK_SYMBOL, SEVERITY_SYMBOLS } from "../symbols";
import type { DiagnosticInfo } from "../types";

interface DiagnosticListProps {
  datasetId: string;
  onShow: (diagnostic: DiagnosticInfo) => void;
}

/** Diagnosen mit Schweregrad (Symbol und Text), Art und Stelle; Klick zeigt die Stelle im XML. */
export function DiagnosticList({ datasetId, onShow }: DiagnosticListProps) {
  const { t } = useI18n();
  const source = useDataSource();
  const { data, errorKey } = useLoad(datasetId, () => source.getDiagnostics(datasetId));
  return (
    <section className="diagnostics" aria-label={t("diagnostics.title")}>
      <h2>{t("diagnostics.title")}</h2>
      {errorKey !== null && <p role="alert">{t(errorKey)}</p>}
      {data !== null && data.length === 0 && (
        <p>
          <span aria-hidden="true">{OK_SYMBOL}</span> {t("diagnostics.none")}
        </p>
      )}
      {data !== null && data.length > 0 && (
        <ul className="issues">
          {data.map((diagnostic) => (
            <li
              key={`${diagnostic.fileId}|${diagnostic.line}|${diagnostic.column}|${diagnostic.key}`}
              className={`issue issue-${diagnostic.severity}`}
            >
              <span className="issue-severity">
                <span aria-hidden="true">{SEVERITY_SYMBOLS[diagnostic.severity]}</span>{" "}
                {t(`severity.${diagnostic.severity}`)}
              </span>{" "}
              <span className="badge">{t(`diagnostics.category.${diagnostic.category}`)}</span>{" "}
              <span className="issue-text">{t(diagnostic.key, diagnostic.params)}</span>
              {diagnostic.line !== null && (
                <>
                  {" "}
                  <button type="button" className="link-button" onClick={() => onShow(diagnostic)}>
                    {t("diagnostics.position", {
                      file: diagnostic.fileName,
                      line: diagnostic.line,
                      column: diagnostic.column ?? 1,
                    })}
                  </button>
                </>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
