import { dayMarker, trimSeconds } from "../format";
import { useI18n } from "../i18n";
import type { JourneyInfo, LookupInfo } from "../types";

interface JourneyListProps {
  /** Die Fahrten der Datei; `null`, solange sie geladen werden. */
  journeys: readonly JourneyInfo[] | null;
  errorKey: string | null;
  /** Die geöffnete Fahrt (Objekt-ID), falls eine gewählt ist. */
  selected: string | null;
  /** Öffnet die Fahrtansicht der Fahrt. */
  onOpenJourney: (objectId: string) => void;
}

function MissingOr({ lookup }: { lookup: LookupInfo }) {
  const { t } = useI18n();
  if (lookup.status === "found") {
    return lookup.text;
  }
  return (
    <span className="lookup-missing">
      {t(`lookup.${lookup.status}`, { ref: lookup.text ?? "" })}
    </span>
  );
}

function Departure({ journey }: { journey: JourneyInfo }) {
  const time = journey.departureTime;
  const offset = journey.departureDayOffset;
  // Nur eine Verschiebung ungleich 0 wird gezeigt („+1“); ein fehlender Wert bleibt leer.
  const days = Number(offset.text);
  const marker = offset.status === "found" && Number.isInteger(days) ? dayMarker(days) : "";
  return (
    <span className="journey-time">
      {time.status === "found" ? trimSeconds(time.text ?? "") : <MissingOr lookup={time} />}
      {marker !== "" && <span className="day-marker"> {marker}</span>}
    </span>
  );
}

/** Fahrten der Datei als schlichte Liste: Produktkategorie und Zugnummer, darunter Abfahrt und Strecke. */
export function JourneyList({
  journeys: data,
  errorKey,
  selected,
  onOpenJourney,
}: JourneyListProps) {
  const { t } = useI18n();
  return (
    <section className="journeys" aria-label={t("journeys.title")}>
      {errorKey !== null && <p role="alert">{t(errorKey)}</p>}
      {data !== null && data.length === 0 && <p>{t("journeys.none")}</p>}
      {data !== null && data.length > 0 && (
        <ul className="journey-items">
          {data.map((journey) => (
            <li key={journey.object.id}>
              <button
                type="button"
                className={`journey-item${journey.object.id === selected ? " selected" : ""}`}
                title={journey.object.xmlId ?? undefined}
                aria-current={journey.object.id === selected}
                onClick={() => onOpenJourney(journey.object.id)}
              >
                <span className="journey-item-head">
                  {journey.category.status === "found" && (
                    <span className="badge category-badge">{journey.category.text}</span>
                  )}
                  <span className="journey-number">
                    {journey.trainNumbers.length === 0 ? (
                      <span className="lookup-missing">{t("lookup.absent")}</span>
                    ) : (
                      journey.trainNumbers.map((number, position) => (
                        <span key={`${number.status}|${number.objectId}`}>
                          {position > 0 && ", "}
                          <MissingOr lookup={number} />
                        </span>
                      ))
                    )}
                  </span>
                </span>
                <span className="journey-item-route">
                  <Departure journey={journey} /> <MissingOr lookup={journey.firstStop} />
                  {" → "}
                  <MissingOr lookup={journey.lastStop} />
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
