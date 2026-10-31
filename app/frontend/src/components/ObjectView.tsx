import { colorOf } from "../colors";
import { useDataSource, useLoad } from "../data";
import { useI18n } from "../i18n";
import { REFERENCE_SYMBOLS } from "../symbols";
import type { FrameColor, PropertyInfo } from "../types";
import { FrameSwatch } from "./FrameLabel";
import { ReferenceList } from "./ReferenceList";

interface ObjectViewProps {
  objectId: string;
  colors: readonly FrameColor[];
  selectedElement: string | null;
  onSelectElement: (elementId: string) => void;
  onNavigate: (objectId: string, elementId?: string) => void;
}

function Attributes({ attributes }: { attributes: Record<string, string> }) {
  const entries = Object.entries(attributes);
  if (entries.length === 0) {
    return null;
  }
  return (
    <span className="attributes">
      {entries.map(([name, value]) => (
        <span key={name} className="attribute">
          <span className="attribute-name">{name}</span>=<code>{value}</code>
        </span>
      ))}
    </span>
  );
}

interface PropertyTreeProps {
  properties: readonly PropertyInfo[];
  selected: string | null;
  onSelect: (elementId: string) => void;
  onNavigate: (objectId: string) => void;
}

/** Kindelemente als Baum; Werte unverändert, NeTEx-Elementname immer sichtbar. */
function PropertyTree({ properties, selected, onSelect, onNavigate }: PropertyTreeProps) {
  const { t } = useI18n();
  return (
    <ul className="property-tree">
      {properties.map((property) => (
        <li key={property.id}>
          <button
            type="button"
            className={property.id === selected ? "property selected" : "property"}
            onClick={() => onSelect(property.id)}
          >
            <span className="property-name">{property.name}</span>
            <Attributes attributes={property.attributes} />
            {property.children.length === 0 && property.text.trim() !== "" && (
              <code className="property-value">{property.text}</code>
            )}
          </button>
          {property.reference !== null && (
            <span className={`property-reference reference-${property.reference.status}`}>
              {" "}
              <span aria-hidden="true">{REFERENCE_SYMBOLS[property.reference.status]}</span>{" "}
              {t(`refs.status.${property.reference.status}`)}
              {property.reference.targetId !== null && (
                <ReferenceGoTo targetId={property.reference.targetId} onNavigate={onNavigate} />
              )}
            </span>
          )}
          {property.children.length > 0 && (
            <PropertyTree
              properties={property.children}
              selected={selected}
              onSelect={onSelect}
              onNavigate={onNavigate}
            />
          )}
        </li>
      ))}
    </ul>
  );
}

function ReferenceGoTo({
  targetId,
  onNavigate,
}: {
  targetId: string;
  onNavigate: (objectId: string) => void;
}) {
  const { t } = useI18n();
  return (
    <>
      {" "}
      <button type="button" className="link-button" onClick={() => onNavigate(targetId)}>
        {t("refs.goTo")} →
      </button>
    </>
  );
}

/** Objektdetail: Typ, ID, Frame (Farbe und Name), Datei und Stelle, Pfad, Eigenschaften. */
export function ObjectView({
  objectId,
  colors,
  selectedElement,
  onSelectElement,
  onNavigate,
}: ObjectViewProps) {
  const { t } = useI18n();
  const source = useDataSource();
  const { data, errorKey } = useLoad(objectId, () => source.getObject(objectId));
  if (errorKey !== null) {
    return <p role="alert">{t(errorKey)}</p>;
  }
  if (data === null) {
    return <p>{t("app.loading")}</p>;
  }
  const info = data.object;
  const color = colorOf(info, colors);
  return (
    <article className="object-view">
      <header>
        <h2>
          <button type="button" className="link-button" onClick={() => onSelectElement(info.id)}>
            {info.name}
          </button>{" "}
          {info.xmlId !== null && <code>{info.xmlId}</code>}
        </h2>
        <dl className="object-facts">
          <dt>{t("object.frame")}</dt>
          <dd>
            {color !== null && <FrameSwatch color={color} />}{" "}
            {info.frame === null && t("object.noFrame")}
            {info.frame !== null && (color === null || info.notRelevant) && info.frame.name}{" "}
            {info.frame !== null && <code>{info.frame.xmlId}</code>}
          </dd>
          {info.version !== null && (
            <>
              <dt>{t("object.version")}</dt>
              <dd>
                <code>{info.version}</code>
              </dd>
            </>
          )}
          <dt>{t("object.position")}</dt>
          <dd>
            {t("object.positionValue", {
              file: info.fileName,
              line: info.line,
              column: info.column,
            })}
          </dd>
          <dt>{t("object.path")}</dt>
          <dd>
            <code className="path">{data.path}</code>
          </dd>
          <dt>{t("object.attributes")}</dt>
          <dd>
            <Attributes attributes={data.attributes} />
          </dd>
        </dl>
      </header>
      {data.reference !== null && (
        <section className="own-reference" aria-label={t("refs.own")}>
          <h3>{t("refs.own")}</h3>
          <ReferenceList
            titleKey="refs.target"
            direction="outgoing"
            references={[data.reference]}
            colors={colors}
            onNavigate={onNavigate}
          />
        </section>
      )}
      <ReferenceList
        titleKey="refs.outgoing"
        direction="outgoing"
        references={data.outgoing}
        colors={colors}
        onNavigate={onNavigate}
      />
      <ReferenceList
        titleKey="refs.incoming"
        direction="incoming"
        references={data.incoming}
        colors={colors}
        onNavigate={onNavigate}
      />
      {data.referencesTruncated && <p className="note">{t("refs.truncated")}</p>}
      <h3>{t("object.properties")}</h3>
      {data.properties.length === 0 ? (
        <p>{t("object.noProperties")}</p>
      ) : (
        <PropertyTree
          properties={data.properties}
          selected={selectedElement}
          onSelect={onSelectElement}
          onNavigate={onNavigate}
        />
      )}
      {data.truncated && <p className="note">{t("object.truncated")}</p>}
    </article>
  );
}
