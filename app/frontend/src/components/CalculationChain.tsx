import { timeWithDay } from "../format";
import { useI18n } from "../i18n";
import type { JourneyViewInfo, StepInfo, StopInfo, TimeInfo } from "../types";
import { Sourced } from "./Sourced";
import type { SourceProps } from "./sourceProps";

interface CalculationChainProps extends SourceProps {
  journey: JourneyViewInfo;
  timeId: string;
}

interface FoundTime {
  time: TimeInfo;
  stop: StopInfo;
}

function findTime(journey: JourneyViewInfo, timeId: string): FoundTime | null {
  for (const stop of journey.stops) {
    for (const time of [stop.arrival, stop.departure]) {
      if (time !== null && time.id === timeId) {
        return { time, stop };
      }
    }
  }
  return null;
}

function stepKey(step: StepInfo): string {
  return `${step.kind}|${step.element?.id ?? "default"}|${step.clock}|${step.dayOffset}`;
}

function Step({ step, ...source }: SourceProps & { step: StepInfo }) {
  const { t } = useI18n();
  return (
    <li className="calc-step">
      <span className="calc-label">{t(`calc.step.${step.kind}`)}</span>{" "}
      {step.default ? (
        <span className="lookup-missing">{t(`calc.default.${step.kind}`)}</span>
      ) : (
        <Sourced element={step.element} {...source}>
          <code>{step.value}</code>
        </Sourced>
      )}
      {step.related.map((item) => (
        <span key={item.id} className="calc-related">
          {" "}
          <Sourced element={item} {...source}>
            {item.name} <code>{item.xmlId}</code>
          </Sourced>
        </span>
      ))}
      {step.viaFromTo && <span className="note"> ({t("calc.viaFromTo")})</span>}
      <span className="calc-result"> = {timeWithDay(step.clock, step.dayOffset, step.utc)}</span>
    </li>
  );
}

/**
 * Rechenkette einer Zeit: jeder Summand mit eigener Quelle (anklickbar) und dem Zwischenstand.
 * Standardwerte sind gekennzeichnet; fehlt ein Summand, steht der Grund da.
 */
export function CalculationChain({ journey, timeId, ...source }: CalculationChainProps) {
  const { t } = useI18n();
  const found = findTime(journey, timeId);
  if (found === null) {
    return null;
  }
  const { time, stop } = found;
  const kind = time.id.startsWith("arrival") ? "arrival" : "departure";
  return (
    <section className="calculation" aria-label={t("calc.title")}>
      <h2>{t("calc.title")}</h2>
      <p>
        {t(`calc.of.${kind}`, { number: stop.position, stop: stop.stopPoint.text ?? "" })}{" "}
        <strong>
          {time.clock === null
            ? t("time.notComputable")
            : timeWithDay(time.clock, time.dayOffset, time.utc)}
        </strong>{" "}
        <span className="note">{t(`calc.status.${time.status}`)}</span>
      </p>
      {time.reason !== null && (
        <p className="calc-reason">
          <Sourced element={time.reason.element} {...source}>
            {t(time.reason.key, time.reason.params)}
          </Sourced>
        </p>
      )}
      <ol className="calc-steps">
        {time.chain.map((step) => (
          <Step key={stepKey(step)} step={step} {...source} />
        ))}
      </ol>
    </section>
  );
}
