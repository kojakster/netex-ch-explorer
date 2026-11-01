import { useRef } from "react";
import { useI18n } from "../i18n";

interface OpenFilesProps {
  onOpen: (files: File[]) => void;
}

/**
 * „Datei öffnen“: der einzige Weg, eigene Dateien zu öffnen (keine Pfadeingabe).
 * Eine XML-Datei, mehrere XML-Dateien oder eine ZIP-Datei; sie gehen an das lokale Backend.
 */
export function OpenFiles({ onOpen }: OpenFilesProps) {
  const { t } = useI18n();
  const input = useRef<HTMLInputElement>(null);
  return (
    <>
      <button type="button" title={t("openFiles.hint")} onClick={() => input.current?.click()}>
        {t("openFiles.button")}
      </button>
      <input
        ref={input}
        type="file"
        multiple
        hidden
        accept=".xml,.zip,application/xml,text/xml,application/zip"
        aria-label={t("openFiles.input")}
        onChange={(event) => {
          const files = Array.from(event.target.files ?? []);
          // Dieselbe Auswahl soll erneut möglich sein.
          event.target.value = "";
          if (files.length > 0) {
            onOpen(files);
          }
        }}
      />
    </>
  );
}
