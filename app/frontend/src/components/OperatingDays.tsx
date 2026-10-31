import { formatDate } from "../format";
import { useI18n } from "../i18n";
import type { ValidityInfo } from "../types";
import { Sourced, ValueText } from "./Sourced";
import type { SourceProps } from "./sourceProps";

interface OperatingDaysProps extends SourceProps {
  validities: readonly ValidityInfo[];
}

/**
 * Betriebstage aus `AvailabilityCondition`: Zeitraum, Anzahl Tage und aufklappbare Liste der Tage.
 * Keine Pauschalaussagen wie „Mo bis Fr“; die Tage stammen allein aus `ValidDayBits`.
 */
export function OperatingDays({ validities, ...source }: OperatingDaysProps) {
  const { t, language } = useI18n();
  if (validities.length === 0) {
    return <span className="lookup-missing">{t("days.none")}</span>;
  }
  return (
    <>
      {validities.map((validity) => {
        const days = validity.days;
        if (days === null) {
          return (
            <div key={validity.ref.id} className="days">
              <Sourced element={validity.ref} {...source}>
                {validity.problem === null ? (
                  t("days.unresolved")
                ) : (
                  <ValueText value={validity.problem} {...source} />
                )}
              </Sourced>
            </div>
          );
        }
        const first = days.firstDay === null ? "" : formatDate(days.firstDay, language);
        const last = days.lastDay === null ? "" : formatDate(days.lastDay, language);
        return (
          <details key={validity.ref.id} className="days">
            <summary>
              {t("days.summary", {
                from: first,
                to: last,
                period: days.periodDays ?? "?",
                count: days.validCount ?? "?",
              })}
            </summary>
            <p className="days-sources">
              <Sourced element={days.condition} {...source}>
                {days.condition.xmlId ?? days.condition.name}
              </Sourced>{" "}
              <Sourced element={days.fromDate} {...source}>
                {first}
              </Sourced>{" "}
              <Sourced element={days.toDate} {...source}>
                {last}
              </Sourced>{" "}
              <Sourced element={days.validDayBits} {...source}>
                {days.validDayBits?.name}
              </Sourced>
            </p>
            {days.daysListed ? (
              <ul className="day-list">
                {days.days.map((day) => (
                  <li key={day}>{formatDate(day, language)}</li>
                ))}
              </ul>
            ) : (
              <p className="note">{t("days.notListed")}</p>
            )}
          </details>
        );
      })}
    </>
  );
}
