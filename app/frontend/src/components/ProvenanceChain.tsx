import { colorOf } from "../colors";
import { useDataSource, useLoad } from "../data";
import { useI18n } from "../i18n";
import type { ChainLink, FrameColor } from "../types";

interface ProvenanceChainProps {
  /** Die markierte Angabe; `null`, solange nichts gewählt ist. */
  elementId: string | null;
  colors: readonly FrameColor[];
  onSelect: (link: ChainLink) => void;
}

/** Herkunftskette als farbige, anklickbare Kästchen in einer Reihe. */
export function ProvenanceChain({ elementId, colors, onSelect }: ProvenanceChainProps) {
  const { t } = useI18n();
  const source = useDataSource();
  const { data, errorKey } = useLoad(elementId, () => {
    if (elementId === null) {
      return Promise.reject(new Error("keine Auswahl"));
    }
    return source.getProvenance(elementId);
  });
  return (
    <section className="provenance" aria-label={t("chain.title")}>
      <h2>{t("chain.title")}</h2>
      {elementId === null && <p className="hint">{t("chain.empty")}</p>}
      {errorKey !== null && <p role="alert">{t(errorKey)}</p>}
      {elementId !== null && data !== null && (
        <ol className="chain">
          {data.map((link) => {
            const color = colorOf(link.object, colors);
            const style =
              color === null ? undefined : { backgroundColor: color.background, color: color.text };
            return (
              <li key={`${link.kind}-${link.object.id}`} className="chain-item">
                <button
                  type="button"
                  className={`chain-box chain-${link.kind}`}
                  style={style}
                  onClick={() => onSelect(link)}
                >
                  <span className="chain-name">{link.object.name}</span>
                  {link.object.xmlId !== null && <code>{link.object.xmlId}</code>}
                  {link.object.notRelevant && link.object.frame !== null && (
                    <span className="chain-frame">{link.object.frame.name}</span>
                  )}
                </button>
              </li>
            );
          })}
        </ol>
      )}
    </section>
  );
}
