import { useI18n } from "../i18n";
import type { LookupInfo } from "../types";

interface LookupValueProps {
  lookup: LookupInfo;
  onSelect: (objectId: string) => void;
}

/** Angabe aus der Datei (anklickbar zur Herkunft) oder der Grund, warum sie fehlt. */
export function LookupValue({ lookup, onSelect }: LookupValueProps) {
  const { t } = useI18n();
  const objectId = lookup.objectId;
  const content =
    lookup.status === "found" ? (
      lookup.text
    ) : (
      <span className="lookup-missing">
        {t(`lookup.${lookup.status}`, { ref: lookup.text ?? "" })}
      </span>
    );
  if (objectId === null) {
    return <span>{content}</span>;
  }
  return (
    <button type="button" className="link-button" onClick={() => onSelect(objectId)}>
      {content}
    </button>
  );
}
