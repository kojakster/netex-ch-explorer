import { timeWithDay } from "../format";
import { useI18n } from "../i18n";
import type { JourneyViewInfo, PartInfo, PartTimeInfo } from "../types";
import { Facilities } from "./Facilities";
import { OperatingDays } from "./OperatingDays";
import { Sourced, ValueText } from "./Sourced";
import type { SourceProps } from "./sourceProps";

interface PartListProps extends SourceProps {
  journey: JourneyViewInfo;
}

function PartTime({ time, ...source }: SourceProps & { time: PartTimeInfo }) {
  const { t } = useI18n();
  const text =
    time.clock === null || time.day === null ? time.time.text : timeWithDay(time.clock, time.day);
  return (
    <>
      <ValueText value={{ ...time.time, text }} {...source} />
      {time.dayOffset.element === null && time.clock !== null && (
        <span className="note"> ({t("part.defaultOffset")})</span>
      )}
      {time.dayOffset.element !== null && (
        <>
          {" "}
          <Sourced element={time.dayOffset.element} {...source}>
            <span className="flag-name">{time.dayOffset.element.name}</span>=
            <code>{time.dayOffset.text}</code>
          </Sourced>
        </>
      )}
    </>
  );
}

function Part({
  part,
  journey,
  ...source
}: SourceProps & { part: PartInfo; journey: JourneyViewInfo }) {
  const { t } = useI18n();
  const stopAt = (position: number | null) =>
    position === null ? null : journey.stops[position - 1];
  const placed = part.startStop.position !== null && part.endStop.position !== null;
  return (
    <li className="part">
      <h4>
        <Sourced element={part.element} {...source}>
          {t("part.title", { number: part.number })}
        </Sourced>{" "}
        <ValueText value={part.purpose} {...source} />
      </h4>
      {part.description.map((text) => (
        <p key={text.element.id} className="part-description">
          {text.lang !== null && <span className="lang">{text.lang}</span>} {text.text}
        </p>
      ))}
      <dl className="part-facts">
        <dt>{t("part.from")}</dt>
        <dd>
          <ValueText value={part.startStop.stop} {...source} />
          {stopAt(part.startStop.position) !== null && (
            <span className="note">
              {" "}
              ({t("part.stopNumber", { number: part.startStop.position ?? 0 })})
            </span>
          )}
          {" · "}
          <PartTime time={part.start} {...source} />
        </dd>
        <dt>{t("part.to")}</dt>
        <dd>
          <ValueText value={part.endStop.stop} {...source} />
          {stopAt(part.endStop.position) !== null && (
            <span className="note">
              {" "}
              ({t("part.stopNumber", { number: part.endStop.position ?? 0 })})
            </span>
          )}
          {" · "}
          <PartTime time={part.end} {...source} />
        </dd>
        {!placed && (
          <>
            <dt>{t("part.placement")}</dt>
            <dd className="note">{t("part.notPlaced")}</dd>
          </>
        )}
        {part.trainNumbers.length > 0 && (
          <>
            <dt>{t("part.trainNumber")}</dt>
            <dd>
              {part.trainNumbers.map((number) => (
                <span key={number.element?.id ?? number.text} className="list-item">
                  <ValueText value={number} {...source} />
                </span>
              ))}
            </dd>
          </>
        )}
        {part.parentJourney.status !== "absent" && (
          <>
            <dt>{t("part.parentJourney")}</dt>
            <dd>
              <ValueText value={part.parentJourney} {...source} />
            </dd>
          </>
        )}
        {part.facilities.length > 0 && (
          <>
            <dt>{t("part.offers")}</dt>
            <dd>
              <Facilities sets={part.facilities} guideCommit={journey.guideCommit} {...source} />
            </dd>
          </>
        )}
        {part.validity.length > 0 && (
          <>
            <dt>{t("part.days")}</dt>
            <dd>
              <OperatingDays validities={part.validity} {...source} />
            </dd>
          </>
        )}
      </dl>
    </li>
  );
}

/** Teilstrecken (`JourneyPart`) mit Zeiten, Tagen, Angeboten und Zuordnung zu den Halten. */
export function PartList({ journey, ...source }: PartListProps) {
  return (
    <ul className="part-list">
      {journey.parts.map((part) => (
        <Part key={part.element.id} part={part} journey={journey} {...source} />
      ))}
    </ul>
  );
}
