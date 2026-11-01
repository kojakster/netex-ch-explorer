import { useI18n } from "../i18n";
import { useShowOrigin } from "../origin";
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

const RAIL_MODE = "rail";

/**
 * Bezeichnung der Kante: „Gleis“ bei `TransportMode` `rail` der Fahrt, fehlt er, der Linie;
 * anderer bekannter Wert „Kante“, kein TransportMode in den Daten „Gleis/Kante“ (keine Annahme).
 * Der Wert selbst ist immer der `PublicCode` der `Quay`.
 */
export function platformKey(journey: JourneyViewInfo): "rail" | "other" | "unknown" {
  const owners = ["journey", "line"].map((role) =>
    journey.transports.find((transport) => transport.role === role),
  );
  const mode = owners.find((transport) => transport?.mode.status === "found")?.mode.text;
  if (mode === undefined || mode === null) {
    return "unknown";
  }
  return mode === RAIL_MODE ? "rail" : "other";
}

type AccessKey = "both" | "boardingOnly" | "alightingOnly" | "none" | "unknown";

function accessKey(stop: StopInfo): AccessKey {
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

/** StopPlace und Quay des Halts mit ihrer Herkunft (nur mit „Herkunft zeigen“). */
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

/** Hinweise zum Halt: Einschränkung des Ein-/Aussteigens in Worten, Bedarfshalt, Verwendung des Halts. */
function StopNotes({
  stop,
  guideCommit,
  ...source
}: SourceProps & { stop: StopInfo; guideCommit: string | null }) {
  const { t } = useI18n();
  const showOrigin = useShowOrigin();
  const access = accessKey(stop);
  const flags = [stop.forBoarding, stop.forAlighting, stop.requestStop].filter(
    (value) => value.element !== null,
  );
  return (
    <>
      {(showOrigin || access !== "both") && (
        <div className={access === "unknown" ? "stop-access lookup-missing" : "stop-access"}>
          {t(`stop.access.${access}`)}
        </div>
      )}
      {stop.requestStop.text === "true" && (
        <div className="stop-request">{t("stop.requestStop")}</div>
      )}
      {!showOrigin && stop.stopUse !== null && (
        <div className="stop-use">
          <Sourced element={stop.stopUse.element} {...source}>
            <code>{stop.stopUse.code}</code>
          </Sourced>{" "}
          <MasterText master={stop.stopUse.master} guideCommit={guideCommit} compact />
        </div>
      )}
      {showOrigin && (
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
      )}
    </>
  );
}

/** Der Fahrplan der Fahrt: an | ab | Halt mit Haltelinie | Gleis/Kante | Hinweis. */
export function StopTable({ journey, selectedTime, onSelectTime, ...source }: StopTableProps) {
  const { t } = useI18n();
  const showOrigin = useShowOrigin();
  if (journey.stops.length === 0) {
    return (
      <p className="lookup-missing">
        {t("stops.none")} <ValueText value={journey.pattern} {...source} />
      </p>
    );
  }
  const lastPosition = journey.stops.length;
  return (
    <div className="table-scroll">
      <table className="stop-table">
        <thead>
          <tr>
            <th>{t("stops.arrival")}</th>
            <th>{t("stops.departure")}</th>
            <th className="line-head" />
            <th>{t("stops.stop")}</th>
            <th>{t(`stops.platform.${platformKey(journey)}`)}</th>
            <th>{t("stops.notes")}</th>
          </tr>
        </thead>
        <tbody>
          {journey.stops.map((stop, row) => (
            <tr
              key={stop.point.id}
              className={`stop-row${row === 0 ? " stop-first" : ""}${row === lastPosition - 1 ? " stop-last" : ""}`}
            >
              <td className="time-col">
                <TimeCell
                  time={stop.arrival}
                  selectedTime={selectedTime}
                  onSelect={(time) => onSelectTime(time, stop)}
                />
              </td>
              <td className="time-col">
                <TimeCell
                  time={stop.departure}
                  selectedTime={selectedTime}
                  onSelect={(time) => onSelectTime(time, stop)}
                  strong
                />
              </td>
              <td aria-hidden="true" className="line-cell" />
              <td className="stop-cell">
                <span className="stop-number">{stop.position}</span>{" "}
                <ValueText value={stop.stopPoint} {...source} className="stop-name" />
                {showOrigin && <Places stop={stop} {...source} />}
              </td>
              <td className="platform-cell">
                <ValueText value={stop.quay} {...source} />
              </td>
              <td className="notes-cell">
                <StopNotes stop={stop} guideCommit={journey.guideCommit} {...source} />
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
