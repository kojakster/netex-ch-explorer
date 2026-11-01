import { type CSSProperties, useId, useState } from "react";
import { colorOf } from "../colors";
import { useDataSource, useLoad } from "../data";
import { useI18n } from "../i18n";
import { MAX_INDENT_LEVEL, type VisibleEntry, visibleEntries } from "../objectTree";
import type { DatasetInfo, FrameColor } from "../types";
import { FrameSwatch } from "./FrameLabel";

const INDENT_REM = 0.9;

interface ObjectTreeProps {
  dataset: DatasetInfo;
  colors: readonly FrameColor[];
  onSelect: (objectId: string) => void;
}

function indentOf(depth: number): CSSProperties {
  return { marginInlineStart: `${Math.min(depth, MAX_INDENT_LEVEL) * INDENT_REM}rem` };
}

/** Objekte nach Frames gegliedert, mit Filter nach Typ und Teiltext in ID oder Name. */
export function ObjectTree({ dataset, colors, onSelect }: ObjectTreeProps) {
  const { t } = useI18n();
  const source = useDataSource();
  const typeId = useId();
  const queryId = useId();
  const [type, setType] = useState("");
  const [query, setQuery] = useState("");
  // Wahl des Benutzers je Frame (Objekt-ID → offen); ohne Wahl gilt die Schwelle.
  const [choices, setChoices] = useState<ReadonlyMap<string, boolean>>(new Map());
  const requestKey = JSON.stringify([dataset.id, type, query.trim()]);
  const { data, errorKey } = useLoad(requestKey, () =>
    source.getObjectTree(dataset.id, { type, q: query.trim() }),
  );
  const toggle = (frameId: string, open: boolean) =>
    setChoices((previous) => new Map(previous).set(frameId, open));

  const frameRows = data === null ? [] : visibleEntries(data.entries, choices);
  const outsideRows = data === null ? [] : visibleEntries(data.outside, choices);

  const renderObject = ({ entry }: VisibleEntry) => {
    const info = entry.object;
    const color = colorOf(info, colors);
    return (
      <li
        key={info.id}
        className={entry.matches ? "tree-object" : "tree-object tree-context"}
        style={indentOf(entry.depth)}
        title={entry.matches ? undefined : t("tree.context")}
      >
        <button type="button" className="link-button" onClick={() => onSelect(info.id)}>
          <span className="object-line">
            <span className="object-type">{info.name}</span>
            {info.label !== null && <span className="object-label">{info.label}</span>}
            {info.notRelevant && color !== null && (
              <>
                {" "}
                <FrameSwatch color={color} />
              </>
            )}
          </span>
          {info.xmlId !== null && <code className="object-id">{info.xmlId}</code>}
        </button>
      </li>
    );
  };

  const renderFrame = ({ entry, objectCount, open }: VisibleEntry) => {
    const info = entry.object;
    const color = colorOf(info, colors);
    const style: CSSProperties = {
      ...indentOf(entry.depth),
      ...(color === null ? {} : { backgroundColor: color.background, color: color.text }),
    };
    return (
      <li key={info.id} className="tree-frame" style={style}>
        <button
          type="button"
          className="tree-toggle"
          aria-expanded={open}
          aria-label={t(open ? "tree.collapse" : "tree.expand", { name: info.name })}
          onClick={() => toggle(info.id, !open)}
        >
          {open ? "▾" : "▸"}
        </button>
        <button
          type="button"
          className="link-button tree-frame-link"
          onClick={() => onSelect(info.id)}
        >
          <span className="object-type">{info.name}</span>
          {info.xmlId !== null && <code className="object-id">{info.xmlId}</code>}
        </button>
        <span className="tree-count">{t("tree.objectCount", { count: objectCount })}</span>
      </li>
    );
  };

  const renderRow = (row: VisibleEntry) =>
    row.entry.isFrame ? renderFrame(row) : renderObject(row);
  const isEmpty = data !== null && data.entries.length === 0 && data.outside.length === 0;

  return (
    <section className="object-search" aria-label={t("search.title")}>
      <div className="search-fields">
        <label htmlFor={typeId}>{t("search.type")}</label>
        <select id={typeId} value={type} onChange={(event) => setType(event.target.value)}>
          <option value="">{t("search.allTypes")}</option>
          {dataset.objectTypes.map((objectType) => (
            <option key={objectType.name} value={objectType.name}>
              {objectType.name} ({objectType.count})
            </option>
          ))}
        </select>
        <label htmlFor={queryId}>{t("search.query")}</label>
        <input
          id={queryId}
          type="search"
          value={query}
          maxLength={200}
          onChange={(event) => setQuery(event.target.value)}
        />
      </div>
      {errorKey !== null && <p role="alert">{t(errorKey)}</p>}
      {data !== null && (
        <>
          <p className="search-count">{t("tree.count", { count: data.total })}</p>
          {data.truncated && (
            <p className="tree-truncated" role="status">
              {t("tree.truncated", { shown: data.shown, total: data.total })}
            </p>
          )}
          {isEmpty && <p className="hint">{t("tree.empty")}</p>}
          {frameRows.length > 0 && <ul className="tree-list">{frameRows.map(renderRow)}</ul>}
          {outsideRows.length > 0 && (
            <>
              <h3 className="tree-group">{t("tree.outside")}</h3>
              <ul className="tree-list">{outsideRows.map(renderRow)}</ul>
            </>
          )}
        </>
      )}
    </section>
  );
}
