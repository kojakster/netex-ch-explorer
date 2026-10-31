import { useId, useState } from "react";
import { useDataSource, useLoad } from "../data";
import { useI18n } from "../i18n";
import type { DatasetInfo } from "../types";

export const PAGE_SIZE = 50;

interface ObjectSearchProps {
  dataset: DatasetInfo;
  onSelect: (objectId: string) => void;
}

/** Einfache Objektsuche nach Typ und Teiltext in ID oder Name, seitenweise. */
export function ObjectSearch({ dataset, onSelect }: ObjectSearchProps) {
  const { t } = useI18n();
  const source = useDataSource();
  const typeId = useId();
  const queryId = useId();
  const [type, setType] = useState("");
  const [query, setQuery] = useState("");
  const [offset, setOffset] = useState(0);
  const requestKey = JSON.stringify([dataset.id, type, query.trim(), offset]);
  const { data, errorKey } = useLoad(requestKey, () =>
    source.searchObjects(dataset.id, { type, q: query.trim(), limit: PAGE_SIZE, offset }),
  );
  const total = data?.total ?? 0;
  return (
    <section className="object-search" aria-label={t("search.title")}>
      <h2>{t("search.title")}</h2>
      <div className="search-fields">
        <label htmlFor={typeId}>{t("search.type")}</label>
        <select
          id={typeId}
          value={type}
          onChange={(event) => {
            setType(event.target.value);
            setOffset(0);
          }}
        >
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
          onChange={(event) => {
            setQuery(event.target.value);
            setOffset(0);
          }}
        />
      </div>
      {errorKey !== null && <p role="alert">{t(errorKey)}</p>}
      {data !== null && (
        <>
          <p className="search-count">
            {t("search.count", {
              total,
              from: total === 0 ? 0 : offset + 1,
              to: Math.min(offset + PAGE_SIZE, total),
            })}
          </p>
          <ul className="search-results">
            {data.items.map((item) => (
              <li key={item.id}>
                <button type="button" className="link-button" onClick={() => onSelect(item.id)}>
                  <span className="object-type">{item.name}</span> <code>{item.xmlId}</code>
                  {item.label !== null && <span className="object-label">{item.label}</span>}
                </button>
              </li>
            ))}
          </ul>
          <div className="pager">
            <button
              type="button"
              disabled={offset === 0}
              onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
            >
              {t("search.previous")}
            </button>
            <button
              type="button"
              disabled={offset + PAGE_SIZE >= total}
              onClick={() => setOffset(offset + PAGE_SIZE)}
            >
              {t("search.next")}
            </button>
          </div>
        </>
      )}
    </section>
  );
}
