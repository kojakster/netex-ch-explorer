import { useDataSource, useLoad } from "../data";
import { useI18n } from "../i18n";
import { LookupValue } from "./Lookup";

interface JourneyListProps {
  datasetId: string;
  onSelect: (objectId: string) => void;
}

/** Liste der Fahrten der Datei: Zugnummer, Linie, Abfahrt, erster und letzter Halt. */
export function JourneyList({ datasetId, onSelect }: JourneyListProps) {
  const { t } = useI18n();
  const source = useDataSource();
  const { data, errorKey } = useLoad(datasetId, () => source.getJourneys(datasetId));
  return (
    <section className="journeys" aria-label={t("journeys.title")}>
      <h2>{t("journeys.title")}</h2>
      {errorKey !== null && <p role="alert">{t(errorKey)}</p>}
      {data !== null && data.length === 0 && <p>{t("journeys.none")}</p>}
      {data !== null && data.length > 0 && (
        <table className="journey-table">
          <thead>
            <tr>
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
                    onClick={() => onSelect(journey.object.id)}
                  >
                    {journey.trainNumbers.length > 0
                      ? journey.trainNumbers.map((number) => number.text ?? "").join(", ")
                      : journey.object.name}
                  </button>
                </td>
                <td>
                  <LookupValue lookup={journey.line} onSelect={onSelect} />
                </td>
                <td>
                  <LookupValue lookup={journey.departureTime} onSelect={onSelect} />
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
