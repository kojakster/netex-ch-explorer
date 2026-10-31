import { useI18n } from "../i18n";
import { SEVERITY_SYMBOLS } from "../symbols";
import type { AppInfo, CheckStep, GuideInfo } from "../types";
import { FrameSwatch } from "./FrameLabel";

interface HelpPageProps {
  appInfo: AppInfo;
  guide: GuideInfo | null;
  onBack: () => void;
}

/** Hilfeseite; veränderliche Teile (Farben, Grau-Liste, Prüfungen) kommen aus den Daten. */
export function HelpPage({ appInfo, guide, onBack }: HelpPageProps) {
  const { t } = useI18n();
  const performed = appInfo.checks.filter((check) => check.status === "performed");
  const notPerformed = appInfo.checks.filter((check) => check.status !== "performed");
  return (
    <article className="help">
      <button type="button" onClick={onBack}>
        {t("app.back")}
      </button>
      <h1>{t("help.title")}</h1>

      <section>
        <h2>{t("help.features")}</h2>
        <dl>
          {appInfo.features.map((feature) => (
            <div key={feature}>
              <dt>{t(`feature.${feature}.title`)}</dt>
              <dd>{t(`feature.${feature}.description`)}</dd>
            </div>
          ))}
        </dl>
      </section>

      <section>
        <h2>{t("help.frameColors")}</h2>
        <p>{t("help.frameColorsText")}</p>
        <table className="help-colors">
          <tbody>
            {appInfo.frameColors.map((color) => (
              <tr key={color.key}>
                <td>
                  <FrameSwatch color={color} />
                </td>
                <td>
                  <code>{color.background}</code> / <code>{color.text}</code>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <h3>{t("help.notRelevant")}</h3>
        <p>{t("help.notRelevantText")}</p>
        <ul className="help-elements">
          {appInfo.notRelevantElements.map((element) => (
            <li key={element}>
              <code>{element}</code>
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h2>{t("help.checks")}</h2>
        <p>{t("help.checksText")}</p>
        <h3>{t("help.checksPerformed")}</h3>
        <CheckList checks={performed} />
        <h3>{t("help.checksNotPerformed")}</h3>
        <CheckList checks={notPerformed} />
      </section>

      <section>
        <h2>{t("help.coreRules")}</h2>
        <p>{t("help.coreRulesText")}</p>
        <dl className="help-core-rules">
          {appInfo.coreRules.map((rule) => (
            <div key={rule.id}>
              <dt>
                {rule.id} <span aria-hidden="true">{SEVERITY_SYMBOLS[rule.severity]}</span>{" "}
                {t(`severity.${rule.severity}`)}
              </dt>
              <dd>
                {t(`coreRule.kind.${rule.kind}`, {
                  context: rule.context,
                  path: rule.targets.join(" | "),
                  allowed: rule.allowed.join(", "),
                })}
                <br />
                {t("help.source")}: <code className="source">{rule.source}</code>
              </dd>
            </div>
          ))}
        </dl>
      </section>

      <section>
        <h2>{t("help.severities")}</h2>
        <dl>
          {appInfo.severities.map((severity) => (
            <div key={severity}>
              <dt>
                <span aria-hidden="true">{SEVERITY_SYMBOLS[severity]}</span>{" "}
                {t(`severity.${severity}`)}
              </dt>
              <dd>{t(`severity.${severity}.description`)}</dd>
            </div>
          ))}
        </dl>
      </section>

      <section>
        <h2>{t("help.guide")}</h2>
        <p>{t("help.guideText")}</p>
        {guide?.commit != null && (
          <p>
            {t("guide.commit")} <code>{guide.commit}</code>
          </p>
        )}
      </section>
    </article>
  );
}

interface CheckListProps {
  checks: readonly CheckStep[];
}

function CheckList({ checks }: CheckListProps) {
  const { t } = useI18n();
  if (checks.length === 0) {
    return <p>{t("help.none")}</p>;
  }
  return (
    <dl className="help-checks">
      {checks.map((check) => (
        <div key={check.id}>
          <dt>{t(`check.${check.id}.title`)}</dt>
          <dd>
            {t(`check.${check.id}.description`)}
            <br />
            {t("help.status")}: {t(`checkStatus.${check.status}`)}
            {check.sources.length > 0 && (
              <>
                <br />
                {t("help.source")}:{" "}
                {check.sources.map((source) => (
                  <code key={source} className="source">
                    {source}
                  </code>
                ))}
              </>
            )}
          </dd>
        </div>
      ))}
    </dl>
  );
}
