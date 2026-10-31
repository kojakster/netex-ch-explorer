import { useI18n } from "../i18n";
import { OK_SYMBOL, SEVERITY_SYMBOLS, UNREADABLE_SYMBOL } from "../symbols";
import type { ExampleInfo } from "../types";

interface ExampleListProps {
  examples: readonly ExampleInfo[];
  selected: string | null;
  onOpen: (name: string) => void;
}

function messageCount(example: ExampleInfo): number {
  return (example.counts.error ?? 0) + (example.counts.warning ?? 0) + (example.counts.info ?? 0);
}

function statusSymbol(example: ExampleInfo): string {
  switch (example.result) {
    case null:
      return "";
    case "clean":
      return OK_SYMBOL;
    case "notes":
      return SEVERITY_SYMBOLS.info;
    case "errors":
    case "check_failed":
      return SEVERITY_SYMBOLS.error;
    case "unreadable":
      return UNREADABLE_SYMBOL;
  }
}

/** Auswahl der Guide-Beispiele mit Status pro Beispiel (Symbol und Text). */
export function ExampleList({ examples, selected, onOpen }: ExampleListProps) {
  const { t } = useI18n();
  return (
    <section className="examples" aria-label={t("examples.title")}>
      <h2>{t("examples.title")}</h2>
      {examples.length === 0 && <p>{t("examples.none")}</p>}
      <ul>
        {examples.map((example) => {
          const count = messageCount(example);
          return (
            <li key={example.name}>
              <button
                type="button"
                className={example.name === selected ? "example selected" : "example"}
                onClick={() => onOpen(example.name)}
                aria-pressed={example.name === selected}
              >
                <span className="example-name">{example.name}</span>
                {example.title !== null && <span className="example-title">{example.title}</span>}
                <span className="example-status">
                  <span aria-hidden="true">{statusSymbol(example)}</span>{" "}
                  {example.result === null
                    ? t("examples.pending")
                    : t(`examples.result.${example.result}`, { count })}
                  {(example.change === "changed" || example.change === "new") && (
                    <>
                      {" · "}
                      <span className="badge">{t(`examples.change.${example.change}`)}</span>
                    </>
                  )}
                </span>
              </button>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
