import { useDataSource, useLoad } from "../data";
import { useI18n } from "../i18n";
import type { FrameColor, ObjectInfo, PropertyInfo } from "../types";
import { FrameSwatch } from "./FrameLabel";

interface ObjectViewProps {
  objectId: string;
  colors: readonly FrameColor[];
  selectedElement: string | null;
  onSelectElement: (elementId: string) => void;
}

function frameColor(info: ObjectInfo, colors: readonly FrameColor[]): FrameColor | null {
  return colors.find((color) => color.key === info.colorKey) ?? null;
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
}

/** Kindelemente als Baum; Werte unverändert, NeTEx-Elementname immer sichtbar. */
function PropertyTree({ properties, selected, onSelect }: PropertyTreeProps) {
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
          {property.children.length > 0 && (
            <PropertyTree properties={property.children} selected={selected} onSelect={onSelect} />
          )}
        </li>
      ))}
    </ul>
  );
}

/** Objektdetail: Typ, ID, Frame (Farbe und Name), Datei und Stelle, Pfad, Eigenschaften. */
export function ObjectView({
  objectId,
  colors,
  selectedElement,
  onSelectElement,
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
  const color = frameColor(info, colors);
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
      <h3>{t("object.properties")}</h3>
      {data.properties.length === 0 ? (
        <p>{t("object.noProperties")}</p>
      ) : (
        <PropertyTree
          properties={data.properties}
          selected={selectedElement}
          onSelect={onSelectElement}
        />
      )}
      {data.truncated && <p className="note">{t("object.truncated")}</p>}
    </article>
  );
}
