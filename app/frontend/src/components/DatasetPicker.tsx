import { useId } from "react";
import { useI18n } from "../i18n";
import type { ExampleInfo } from "../types";
import { exampleStatusSymbol } from "./ExampleList";
import { OpenFiles } from "./OpenFiles";

interface DatasetPickerProps {
  examples: readonly ExampleInfo[];
  /** Name des geöffneten Beispiels; `null` bei eigenen Dateien oder ohne Datensatz. */
  selected: string | null;
  onOpenExample: (name: string) => void;
  onOpenFiles: (files: File[]) => void;
}

/** Datensatz-Wahl der Kopfzeile: Auswahlliste der Guide-Beispiele mit Status und „Datei öffnen …“. */
export function DatasetPicker({
  examples,
  selected,
  onOpenExample,
  onOpenFiles,
}: DatasetPickerProps) {
  const { t } = useI18n();
  const id = useId();
  return (
    <div className="dataset-picker">
      <label htmlFor={id}>{t("picker.label")}</label>
      <select
        id={id}
        value={selected ?? ""}
        onChange={(event) => {
          if (event.target.value !== "") {
            onOpenExample(event.target.value);
          }
        }}
      >
        <option value="">{t("picker.placeholder")}</option>
        {examples.map((example) => (
          <option key={example.name} value={example.name}>
            {`${exampleStatusSymbol(example)} ${example.name}`.trim()}
          </option>
        ))}
      </select>
      <OpenFiles onOpen={onOpenFiles} />
    </div>
  );
}
