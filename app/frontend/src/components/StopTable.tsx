import { useI18n } from "../i18n";
import type { JourneyViewInfo, StopInfo, TimeInfo } from "../types";
import { Facilities } from "./Facilities";
import { MasterText } from "./MasterText";
import { Sourced, ValueText } from "./Sourced";
import type { SourceProps } from "./sourceProps";
import { TimeCell } from "./TimeCell";

interface StopTableProps extends SourceProps {
  journey: JourneyViewInfo;
  selectedTime: string | null;
  onSelectTime: (time: TimeInfo, stop: StopInfo) => void;
}

function accessKey(stop: StopInfo): string {
  const boarding = stop.forBoarding.text;
  const alighting = stop.forAlighting.text;
  if (boarding === "true" && alighting === "true") {
    return "both";
  }
  if (boarding === "true" && alighting === "false") {
    return "boardingOnly";
  }
  if (boarding === "false" && alighting === "true") {
    return "alightingOnly";
  }
  return boarding === "false" && alighting === "false" ? "none" : "unknown";
}

function Places({ stop, ...source }: SourceProps & { stop: StopInfo }) {
  const { t } = useI18n();
  const place = stop.stopPlace;
  const quay = stop.quay;
  if (place.status === "external_or_unloaded" && quay.status === "external_or_unloaded") {
    return (
      <div className="stop-places lookup-missing">
        {t("stop.notInFile")} <code>{place.text}</code>
      </div>
    );
  }
  return (
    <dl className="stop-places">
      <dt>{t("stop.stopPlace")}</dt>
      <dd>
        <ValueText value={place} {...source} />
      </dd>
      <dt>{t("stop.quay")}</dt>
      <dd>
        <ValueText value={quay} {...source} />
      </dd>
    </dl>
  );
}

function Access({
  stop,
  guideCommit,
  ...source
}: SourceProps & { stop: StopInfo; guideCommit: string | null }) {
  const { t } = useI18n();
  const flags = [stop.forBoarding, stop.forAlighting, stop.requestStop].filter(
    (value) => value.element !== null,
  );
  return (
    <>
      <div className="stop-access">{t(`stop.access.${accessKey(stop)}`)}</div>
      {stop.requestStop.text === "true" && (
        <div className="stop-request">{t("stop.requestStop")}</div>
      )}
      <div className="stop-flags">
        {flags.map((value) => (
          <Sourced key={value.element?.id} element={value.element} {...source} className="flag">
            <span className="flag-name">{value.element?.name}</span>=<code>{value.text}</code>
          </Sourced>
        ))}
        {stop.stopUse !== null && (
          <span className="flag-use">
            <Sourced element={stop.stopUse.element} {...source} className="flag">
              <span className="flag-name">{stop.stopUse.element.name}</span>=
              <code>{stop.stopUse.code}</code>
            </Sourced>{" "}
            <MasterText master={stop.stopUse.master} guideCommit={guideCommit} compact />
          </span>
        )}
      </div>
    </>
  );
}

/** Der Fahrplan der Fahrt: Halt, Ein-/Aussteigen, Ankunft, Abfahrt und Angebote je Teilstrecke. */
export function StopTable({ journey, selectedTime, onSelectTime, ...source }: StopTableProps) {
  const { t } = useI18n();
  if (journey.stops.length === 0) {
    return (
      <p className="lookup-missing">
        {t("stops.none")} <ValueText value={journey.pattern} {...source} />
      </p>
    );
  }
  return (
    <div className="table-scroll">
      <table className="stop-table">
        <thead>
          <tr>
            <th>{t("stops.stop")}</th>
            <th>{t("stops.access")}</th>
            <th>{t("stops.arrival")}</th>
            <th>{t("stops.departure")}</th>
            <th>{t("stops.offers")}</th>
          </tr>
        </thead>
        <tbody>
          {journey.stops.map((stop) => (
            <tr key={stop.point.id}>
              <td>
                <span className="stop-number">{stop.position}</span>{" "}
                <ValueText value={stop.stopPoint} {...source} className="stop-name" />
                <Places stop={stop} {...source} />
              </td>
              <td>
                <Access stop={stop} guideCommit={journey.guideCommit} {...source} />
              </td>
              <td>
                <TimeCell
                  time={stop.arrival}
                  selectedTime={selectedTime}
                  onSelect={(time) => onSelectTime(time, stop)}
                />
              </td>
              <td>
                <TimeCell
                  time={stop.departure}
                  selectedTime={selectedTime}
                  onSelect={(time) => onSelectTime(time, stop)}
                />
              </td>
              <td>
                {stop.partNumbers.map((number) => {
                  const part = journey.parts.find((item) => item.number === number);
                  return (
                    <div key={number} className="stop-offer">
                      <span className="badge">{t("part.short", { number })}</span>{" "}
                      <Facilities
                        sets={part?.facilities ?? []}
                        guideCommit={journey.guideCommit}
                        compact
                        {...source}
                      />
                    </div>
                  );
                })}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
