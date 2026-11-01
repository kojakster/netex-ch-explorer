import { type ReactNode, useRef } from "react";
import { formatDate } from "../format";
import { useI18n } from "../i18n";
import { OriginContext } from "../origin";
import { SEVERITY_SYMBOLS } from "../symbols";
import type {
  CategoryInfo,
  DiagnosticInfo,
  JourneyViewInfo,
  Severity,
  StopInfo,
  TimeInfo,
  TransportInfo,
  ValueInfo,
} from "../types";
import { DiagnosticItems } from "./DiagnosticList";
import { Facilities } from "./Facilities";
import { FrameLegend } from "./FrameLegend";
import { MasterText } from "./MasterText";
import { NoticeList } from "./NoticeList";
import { OperatingDays } from "./OperatingDays";
import { PartList } from "./PartList";
import { ReasonText, Sourced, ValueText } from "./Sourced";
import { StopTable } from "./StopTable";
import type { SourceProps } from "./sourceProps";

interface JourneyViewProps extends SourceProps {
  journey: JourneyViewInfo;
  selectedTime: string | null;
  onSelectTime: (time: TimeInfo, stop: StopInfo) => void;
  onShowDiagnostic: (diagnostic: DiagnosticInfo) => void;
  /** Schalter „Herkunft zeigen“ (Zustand liegt in der Anwendung, damit er beim Wechsel bleibt). */
  showOrigin: boolean;
  onShowOriginChange: (showOrigin: boolean) => void;
}

const SEVERITY_ORDER: readonly Severity[] = ["error", "warning", "info"];

function Transport({ transport, ...source }: SourceProps & { transport: TransportInfo }) {
  const { t } = useI18n();
  return (
    <div className="transport">
      <span className="badge">{t(`journey.role.${transport.role}`)}</span>{" "}
      {transport.mode.element !== null && (
        <>
          <Sourced element={transport.mode.element} {...source} className="flag">
            <span className="flag-name">{transport.mode.element.name}</span>=
            <code>{transport.mode.text}</code>
          </Sourced>{" "}
          <span className="master master-none">{t("master.none")}</span>
        </>
      )}
      {transport.submode.element !== null && (
        <>
          {" "}
          <Sourced element={transport.submode.element} {...source} className="flag">
            <span className="flag-name">{transport.submodeType}</span>=
            <code>{transport.submode.text}</code>
          </Sourced>{" "}
          <span className="master master-none">{t("master.none")}</span>
        </>
      )}
      {transport.mode.element === null && transport.submode.element === null && (
        <span className="lookup-missing">{t("lookup.absent")}</span>
      )}
    </div>
  );
}

function Category({
  category,
  guideCommit,
  ...source
}: SourceProps & { category: CategoryInfo; guideCommit: string | null }) {
  const { t } = useI18n();
  return (
    <div className="category">
      <span className="badge">{t(`journey.role.${category.role}`)}</span>{" "}
      {category.target === null ? (
        <ReasonText
          element={category.ref}
          problem={category.problem}
          fallback={t("lookup.absent")}
          {...source}
        />
      ) : (
        <>
          <ValueText value={category.shortName} {...source} className="category-code" />{" "}
          {category.names.map((name) => (
            <span key={name.element.id} className="category-name">
              {name.lang !== null && <span className="lang">{name.lang}</span>} {name.text}{" "}
            </span>
          ))}
          <MasterText master={category.master} guideCommit={guideCommit} />
        </>
      )}
    </div>
  );
}

interface TermProps {
  /** Verständliche Bezeichnung; der NeTEx-Name steht klein dahinter. */
  label: string;
  netex: string;
}

function Term({ label, netex }: TermProps) {
  return (
    <dt>
      {label} <span className="netex-name">{`· ${netex}`}</span>
    </dt>
  );
}

/** Produktkategorie für das Abzeichen im Kopf: die der Fahrt, sonst die der Linie. */
function badgeCategory(journey: JourneyViewInfo): ValueInfo | null {
  const roles = ["journey", "line"];
  for (const role of roles) {
    const category = journey.categories.find((item) => item.role === role);
    if (category !== undefined && category.shortName.status === "found") {
      return category.shortName;
    }
  }
  return null;
}

function severityCount(diagnostics: readonly DiagnosticInfo[], severity: Severity): number {
  return diagnostics.filter((diagnostic) => diagnostic.severity === severity).length;
}

/** Betriebstage und Gültigkeit im Kopf: die Zahlen der AvailabilityCondition, nichts Pauschales. */
function HeaderDays({ journey, ...source }: SourceProps & { journey: JourneyViewInfo }) {
  const { t, language } = useI18n();
  if (journey.validities.length === 0) {
    return <span className="lookup-missing">{t("days.none")}</span>;
  }
  return (
    <>
      {journey.validities.map((validity) => {
        const days = validity.days;
        if (days === null) {
          return (
            <span key={validity.ref.id} className="header-fact">
              <ReasonText
                element={validity.ref}
                problem={validity.problem}
                fallback={t("days.unresolved")}
                {...source}
              />
            </span>
          );
        }
        const first = days.firstDay === null ? "" : formatDate(days.firstDay, language);
        const last = days.lastDay === null ? "" : formatDate(days.lastDay, language);
        return (
          <span key={validity.ref.id} className="header-fact">
            <Sourced element={days.condition} {...source}>
              {t("header.validity", { from: first, to: last })}
            </Sourced>
            {" · "}
            <Sourced element={days.validDayBits ?? days.condition} {...source}>
              {t("header.days", { count: days.validCount ?? "?", period: days.periodDays ?? "?" })}
            </Sourced>
          </span>
        );
      })}
    </>
  );
}

function JourneyHeader({
  journey,
  scrollToFindings,
  ...source
}: SourceProps & { journey: JourneyViewInfo; scrollToFindings: () => void }) {
  const { t } = useI18n();
  const category = badgeCategory(journey);
  const first = journey.stops[0];
  const last = journey.stops[journey.stops.length - 1];
  return (
    <header className="journey-head">
      <div className="journey-head-main">
        <h2>
          {category !== null && (
            <ValueText value={category} {...source} className="badge category-badge badge-large" />
          )}{" "}
          {journey.trainNumbers.length === 0 ? (
            <Sourced element={journey.journey} {...source} className="journey-number-large">
              <span className="lookup-missing">{t("lookup.absent")}</span>
            </Sourced>
          ) : (
            journey.trainNumbers.map((number) => (
              <span key={number.element?.id ?? number.text} className="list-item">
                <ValueText value={number} {...source} className="journey-number-large" />
              </span>
            ))
          )}
        </h2>
        {first !== undefined && last !== undefined && (
          <p className="journey-route">
            <ValueText value={first.stopPoint} {...source} />
            {" → "}
            <ValueText value={last.stopPoint} {...source} />
          </p>
        )}
        <p className="journey-facts-line">
          <span className="header-fact">
            {t("journey.operator")}: <ValueText value={journey.operator} {...source} />
          </span>
          <HeaderDays journey={journey} {...source} />
        </p>
      </div>
      <div className="journey-counts">
        {SEVERITY_ORDER.map((severity) => {
          const count = severityCount(journey.diagnostics, severity);
          return count === 0 ? null : (
            <button
              key={severity}
              type="button"
              className={`count-badge count-${severity}`}
              onClick={scrollToFindings}
            >
              <span aria-hidden="true">{SEVERITY_SYMBOLS[severity]}</span>{" "}
              {t(`severity.${severity}`)} {count}
            </button>
          );
        })}
      </div>
    </header>
  );
}

function MoreDetails({
  journey,
  ...source
}: SourceProps & { journey: JourneyViewInfo }): ReactNode {
  const { t } = useI18n();
  return (
    <details className="more-details">
      <summary>{t("journey.more")}</summary>
      <dl className="journey-facts">
        <Term label={t("journey.trainNumber")} netex="TrainNumber" />
        <dd>
          {journey.trainNumbers.length === 0 ? (
            <span className="lookup-missing">{t("lookup.absent")}</span>
          ) : (
            journey.trainNumbers.map((number) => (
              <span key={number.element?.id ?? number.text} className="list-item">
                <ValueText value={number} {...source} />
              </span>
            ))
          )}
        </dd>
        {journey.privateCodes.length > 0 && (
          <>
            <Term label={t("journey.privateCode")} netex="PrivateCode" />
            <dd>
              {journey.privateCodes.map((code) => (
                <span key={code.element.id} className="list-item">
                  <Sourced element={code.element} {...source}>
                    {code.codeType !== null && <span className="flag-name">{code.codeType}=</span>}
                    <code>{code.value}</code>
                  </Sourced>
                </span>
              ))}
            </dd>
          </>
        )}
        <Term label={t("journey.operator")} netex="Operator" />
        <dd>
          <ValueText value={journey.operator} {...source} />
        </dd>
        <Term label={t("journey.line")} netex="Line" />
        <dd>
          <ValueText value={journey.line} {...source} />
        </dd>
        <Term label={t("journey.transport")} netex="TransportMode" />
        <dd>
          {journey.transports.map((transport) => (
            <Transport key={transport.owner.id} transport={transport} {...source} />
          ))}
        </dd>
        <Term label={t("journey.category")} netex="TypeOfProductCategory" />
        <dd>
          {journey.categories.length === 0 ? (
            <span className="lookup-missing">{t("lookup.absent")}</span>
          ) : (
            journey.categories.map((category) => (
              <Category
                key={category.ref.id}
                category={category}
                guideCommit={journey.guideCommit}
                {...source}
              />
            ))
          )}
        </dd>
        <Term label={t("journey.pattern")} netex="ServiceJourneyPattern" />
        <dd>
          <ValueText value={journey.pattern} {...source} />
        </dd>
        <Term label={t("journey.timeDemand")} netex="TimeDemandType" />
        <dd>
          <ValueText value={journey.timeDemandType} {...source} />
        </dd>
        <Term label={t("journey.days")} netex="AvailabilityCondition" />
        <dd>
          <OperatingDays validities={journey.validities} {...source} />
        </dd>
      </dl>

      {journey.facilities.length > 0 && (
        <section aria-label={t("offers.title")}>
          <h3>
            {t("offers.title")} <span className="netex-name">{"· ServiceFacilitySet"}</span>
          </h3>
          <Facilities sets={journey.facilities} guideCommit={journey.guideCommit} {...source} />
        </section>
      )}

      {journey.parts.length > 0 && (
        <section aria-label={t("parts.title")}>
          <h3>
            {t("parts.title")} <span className="netex-name">{"· JourneyPart"}</span>
          </h3>
          <PartList journey={journey} {...source} />
        </section>
      )}

      {journey.notices.length > 0 && (
        <section aria-label={t("notices.title")}>
          <h3>
            {t("notices.title")} <span className="netex-name">{"· Notice"}</span>
          </h3>
          <NoticeList journey={journey} {...source} />
        </section>
      )}
    </details>
  );
}

/** Die Fahrt als Fahrplananzeige: Kopf, Fahrplantafel, weitere Angaben (eingeklappt), Befunde. */
export function JourneyView({
  journey,
  selectedTime,
  onSelectTime,
  onShowDiagnostic,
  showOrigin,
  onShowOriginChange,
  ...source
}: JourneyViewProps) {
  const { t } = useI18n();
  const findings = useRef<HTMLElement>(null);
  const scrollToFindings = () => findings.current?.scrollIntoView?.({ block: "start" });
  return (
    <OriginContext.Provider value={showOrigin}>
      <article className="journey-view">
        <JourneyHeader journey={journey} scrollToFindings={scrollToFindings} {...source} />

        <div className="origin-bar">
          <label className="origin-switch">
            <input
              type="checkbox"
              checked={showOrigin}
              onChange={(event) => onShowOriginChange(event.target.checked)}
            />{" "}
            {t("journey.showOrigin")}
          </label>
          {showOrigin && <span className="note">{t("journey.showOriginHint")}</span>}
        </div>
        {showOrigin && <FrameLegend colors={source.colors} />}

        <section className="timetable" aria-label={t("stops.title")}>
          <StopTable
            journey={journey}
            selectedTime={selectedTime}
            onSelectTime={onSelectTime}
            {...source}
          />
        </section>
        <p className="note timetable-note">{t("stops.timesNote")}</p>

        <MoreDetails journey={journey} {...source} />

        <section ref={findings} className="findings" aria-label={t("journey.diagnostics")}>
          <h3>{t("journey.diagnostics")}</h3>
          {journey.diagnostics.length === 0 ? (
            <p className="note">{t("diagnostics.none")}</p>
          ) : (
            <DiagnosticItems diagnostics={journey.diagnostics} onShow={onShowDiagnostic} />
          )}
        </section>
      </article>
    </OriginContext.Provider>
  );
}
