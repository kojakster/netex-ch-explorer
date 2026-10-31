import { useI18n } from "../i18n";
import type { JourneyInfo } from "../types";
import { LookupValue } from "./Lookup";

interface JourneyListProps {
  /** Die Fahrten der Datei; `null`, solange sie geladen werden. */
  journeys: readonly JourneyInfo[] | null;
  errorKey: string | null;
  /** Wählt das Objekt hinter einer Angabe. */
  onSelect: (objectId: string) => void;
  /** Öffnet die Fahrtansicht der Fahrt. */
  onOpenJourney: (objectId: string) => void;
}

/** Liste der Fahrten der Datei: Zugnummer, Linie, Abfahrt, erster und letzter Halt. */
export function JourneyList({
  journeys: data,
  errorKey,
  onSelect,
  onOpenJourney,
}: JourneyListProps) {
  const { t } = useI18n();
  return (
    <section className="journeys" aria-label={t("journeys.title")}>
      <h2>{t("journeys.title")}</h2>
      {errorKey !== null && <p role="alert">{t(errorKey)}</p>}
      {data !== null && data.length === 0 && <p>{t("journeys.none")}</p>}
      {data !== null && data.length > 0 && (
        <table className="journey-table">
          <thead>
            <tr>
              <th>{t("journeys.journey")}</th>
              <th>{t("journeys.trainNumber")}</th>
              <th>{t("journeys.line")}</th>
              <th>{t("journeys.departure")}</th>
              <th>{t("journeys.from")}</th>
              <th>{t("journeys.to")}</th>
            </tr>
          </thead>
          <tbody>
            {data.map((journey) => (
              <tr key={journey.object.id}>
                <td>
                  <button
                    type="button"
                    className="link-button"
                    title={journey.object.xmlId ?? undefined}
                    onClick={() => onOpenJourney(journey.object.id)}
                  >
                    {journey.object.name}
                  </button>
                </td>
                <td>
                  {journey.trainNumbers.length === 0 ? (
                    <span className="lookup-missing">{t("lookup.absent")}</span>
                  ) : (
                    journey.trainNumbers.map((number, position) => (
                      <span key={`${number.status}|${number.objectId}`}>
                        {position > 0 && ", "}
                        <LookupValue lookup={number} onSelect={onSelect} />
                      </span>
                    ))
                  )}
                </td>
                <td>
                  <LookupValue lookup={journey.line} onSelect={onSelect} />
                </td>
                <td>
                  <LookupValue lookup={journey.departureTime} onSelect={onSelect} />
                  {journey.departureDayOffset.status === "found" && (
                    <>
                      {" "}
                      <LookupValue
                        lookup={{
                          ...journey.departureDayOffset,
                          text: t("journeys.dayOffset", {
                            offset: journey.departureDayOffset.text ?? "",
                          }),
                        }}
                        onSelect={onSelect}
                      />
                    </>
                  )}
                </td>
                <td>
                  <LookupValue lookup={journey.firstStop} onSelect={onSelect} />
                </td>
                <td>
                  <LookupValue lookup={journey.lastStop} onSelect={onSelect} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
