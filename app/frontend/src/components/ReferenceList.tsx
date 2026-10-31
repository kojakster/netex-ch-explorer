import { colorOf } from "../colors";
import { useI18n } from "../i18n";
import { REFERENCE_SYMBOLS } from "../symbols";
import type { FrameColor, ObjectInfo, ReferenceInfo } from "../types";
import { FrameSwatch } from "./FrameLabel";

interface ReferenceListProps {
  titleKey: string;
  direction: "outgoing" | "incoming";
  references: readonly ReferenceInfo[];
  colors: readonly FrameColor[];
  onNavigate: (objectId: string, elementId?: string) => void;
}

interface ObjectLinkProps {
  info: ObjectInfo;
  colors: readonly FrameColor[];
  onClick: () => void;
}

/** Objekt mit Farbe seines Frames (und Frame-Name als Text), Typ und ID; anklickbar. */
function ObjectLink({ info, colors, onClick }: ObjectLinkProps) {
  const color = colorOf(info, colors);
  return (
    <>
      {color !== null && <FrameSwatch color={color} />}{" "}
      <button type="button" className="link-button" onClick={onClick}>
        {info.name}
        {info.xmlId !== null && (
          <>
            {" "}
            <code className="reference-id">{info.xmlId}</code>
          </>
        )}
      </button>
    </>
  );
}

/** Ausgehende oder eingehende Verweise als farbige, anklickbare Liste (Farbe des Gegen-Frames). */
export function ReferenceList({
  titleKey,
  direction,
  references,
  colors,
  onNavigate,
}: ReferenceListProps) {
  const { t } = useI18n();
  return (
    <section className="reference-list" aria-label={t(titleKey)}>
      <h3>{t(titleKey)}</h3>
      {references.length === 0 ? (
        <p>{t("refs.none")}</p>
      ) : (
        <ul>
          {references.map((reference) => {
            // Ausgehend ist das Ziel die Gegenseite, eingehend das Objekt mit dem Verweis
            // (ohne umschliessendes Objekt das Ref-Element selbst).
            const other =
              direction === "outgoing" ? reference.target : (reference.owner ?? reference.element);
            return (
              <li key={reference.element.id} className={`reference reference-${reference.status}`}>
                <button
                  type="button"
                  className="link-button reference-element"
                  onClick={() =>
                    onNavigate(reference.owner?.id ?? reference.element.id, reference.element.id)
                  }
                >
                  {reference.element.name}
                </button>{" "}
                <span className="reference-status">
                  <span aria-hidden="true">{REFERENCE_SYMBOLS[reference.status]}</span>{" "}
                  {t(`refs.status.${reference.status}`)}
                </span>{" "}
                {other !== null ? (
                  <ObjectLink info={other} colors={colors} onClick={() => onNavigate(other.id)} />
                ) : (
                  <>
                    <code>{reference.ref}</code>{" "}
                    <span className="note">
                      {t("refs.expected", { types: reference.expected.join(", ") })}
                    </span>
                  </>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
