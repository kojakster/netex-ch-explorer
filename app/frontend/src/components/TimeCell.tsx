import { dayMarker, trimSeconds } from "../format";
import { useI18n } from "../i18n";
import type { TimeInfo } from "../types";

interface TimeCellProps {
  time: TimeInfo | null;
  selectedTime: string | null;
  onSelect: (time: TimeInfo) => void;
  /** Die Abfahrt steht fett, die Ankunft normal. */
  strong?: boolean;
}

/** Symbol für berechnete Zeiten (Summe aus DepartureTime, RunTime und WaitTime). */
export const CALCULATED_SYMBOL = "Σ";

/** Eine Zeit im Fahrplan: berechnete Zeiten mit Symbol, „+1“/„−1“ nur bei anderem Tag; ein Klick zeigt die Rechenkette. */
export function TimeCell({ time, selectedTime, onSelect, strong = false }: TimeCellProps) {
  const { t } = useI18n();
  if (time === null) {
    return <span className="time-none">{"–"}</span>;
  }
  const selected = selectedTime === time.id ? " selected" : "";
  const weight = strong ? " time-strong" : "";
  if (time.status === "not_computable" || time.clock === null) {
    return (
      <button
        type="button"
        className={`time-button time-failed${weight}${selected}`}
        onClick={() => onSelect(time)}
      >
        <span className="time-missing">{t("time.notComputable")}</span>
        {time.reason !== null && (
          <span className="time-reason">{t(time.reason.key, time.reason.params)}</span>
        )}
      </button>
    );
  }
  const marker = dayMarker(time.dayOffset);
  return (
    <button
      type="button"
      className={`time-button${weight}${selected}`}
      onClick={() => onSelect(time)}
    >
      <span className="time-value">{trimSeconds(time.clock)}</span>
      {marker !== "" && (
        <span
          className="day-marker"
          title={time.offsetOrigin === null ? undefined : t(`time.offset.${time.offsetOrigin}`)}
        >
          {marker}
        </span>
      )}
      {time.status === "computed" && (
        <span className="time-calc" role="img" aria-label={t("time.calculated")}>
          {CALCULATED_SYMBOL}
        </span>
      )}
    </button>
  );
}
