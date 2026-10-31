import { type Translate, useI18n } from "../i18n";
import { OK_SYMBOL, SEVERITY_SYMBOLS, UNREADABLE_SYMBOL } from "../symbols";
import type { DatasetInfo, Detection, FileInfo, Issue, ValidationInfo } from "../types";

const SHORT_COMMIT_LENGTH = 7;

interface DatasetPanelProps {
  dataset: DatasetInfo;
  validating: boolean;
  validationErrorKey: string | null;
  onValidate: () => void;
}

/** Ergebnis der Versionserkennung einer Datei mit Begründung. */
export function DetectionView({ detection }: { detection: Detection }) {
  const { t } = useI18n();
  return (
    <div className="detection">
      {detection.status !== "detected" || detection.profile !== "ch_2_0" ? (
        <p>{t("detection.notChecked")}</p>
      ) : null}
      <p>{t("detection.reasons")}</p>
      <ul>
        {detection.reasons.map((reason) => (
          <li key={`${reason.key}|${JSON.stringify(reason.params)}`}>
            <span className="badge">{t(`detection.evidence.${reason.evidence}`)}</span>{" "}
            {t(reason.key, reason.params)}
          </li>
        ))}
      </ul>
    </div>
  );
}

function FileEntry({ file }: { file: FileInfo }) {
  const { t } = useI18n();
  const detection = file.detection;
  return (
    <li>
      <span aria-hidden="true">{file.readable ? OK_SYMBOL : UNREADABLE_SYMBOL}</span>{" "}
      <span className="file-name">{file.name}</span>{" "}
      {!file.readable && (
        <span className="badge">
          {t(file.size === 0 && file.elements === 0 ? "dataset.noContent" : "dataset.unreadable")}
        </span>
      )}
      {file.readable && detection !== null && (
        <details>
          <summary>
            {t(`detection.status.${detection.status}`, {
              profile:
                detection.profile === null ? "" : t(`detection.profile.${detection.profile}`),
            })}
          </summary>
          <DetectionView detection={detection} />
        </details>
      )}
    </li>
  );
}

function reasonText(t: Translate, issue: Issue | null): string {
  return issue === null ? "" : t(issue.key, issue.params);
}

function ValidationResult({
  validation,
  files,
}: {
  validation: ValidationInfo;
  files: FileInfo[];
}) {
  const { t } = useI18n();
  const commit = validation.guideCommit?.slice(0, SHORT_COMMIT_LENGTH) ?? t("guide.unknown");
  const names = new Map(files.map((file) => [file.id, file.name]));
  return (
    <div className="validation-result">
      <p>
        <strong>{t("validation.result", { commit })}</strong>
      </p>
      <p>{t("validation.scope")}</p>
      <ul>
        {validation.steps.map((step) => (
          <li key={step.id}>
            <span aria-hidden="true">{step.performed ? OK_SYMBOL : SEVERITY_SYMBOLS.warning}</span>{" "}
            {t(`check.${step.id}.title`)}:{" "}
            {step.performed ? t("validation.performed") : reasonText(t, step.reason)}
          </li>
        ))}
      </ul>
      <ul>
        {validation.files
          .filter((file) => !file.checked)
          .map((file) => (
            <li key={file.fileId}>
              <span aria-hidden="true">{SEVERITY_SYMBOLS.info}</span>{" "}
              {t("validation.fileSkipped", {
                file: names.get(file.fileId) ?? String(file.fileId),
                reason: reasonText(t, file.reason),
              })}
            </li>
          ))}
      </ul>
    </div>
  );
}

/** Geöffnete Dateien mit Versionserkennung, Knopf „Prüfen“ und Ergebnis der Prüfung. */
export function DatasetPanel({
  dataset,
  validating,
  validationErrorKey,
  onValidate,
}: DatasetPanelProps) {
  const { t } = useI18n();
  const checkable = dataset.files.some(
    (file) => file.detection?.status === "detected" && file.detection.profile === "ch_2_0",
  );
  return (
    <section className="dataset-panel" aria-label={t("dataset.title")}>
      <h2>{t("dataset.title")}</h2>
      <ul className="dataset-files">
        {dataset.files.map((file) => (
          <FileEntry key={file.id} file={file} />
        ))}
      </ul>
      <button type="button" onClick={onValidate} disabled={validating || !checkable}>
        {validating ? t("validation.running") : t("validation.start")}
      </button>
      {!checkable && <p>{t("validation.notCheckable")}</p>}
      {validationErrorKey !== null && <p role="alert">{t(validationErrorKey)}</p>}
      {dataset.validation === null ? (
        checkable && <p>{t("validation.notYet")}</p>
      ) : (
        <ValidationResult validation={dataset.validation} files={dataset.files} />
      )}
    </section>
  );
}
