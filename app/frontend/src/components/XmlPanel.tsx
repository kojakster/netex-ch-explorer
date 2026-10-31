import { useDataSource, useLoad } from "../data";
import { useI18n } from "../i18n";
import type { FrameColor } from "../types";
import { XmlView } from "./XmlView";

export type XmlTarget =
  | { kind: "object"; objectId: string }
  | { kind: "position"; datasetId: string; file: number; line: number; column: number };

interface XmlPanelProps {
  target: XmlTarget | null;
  colors: readonly FrameColor[];
}

/** Lädt den XML-Ausschnitt zum gewählten Element oder zur gewählten Stelle. */
export function XmlPanel({ target, colors }: XmlPanelProps) {
  const { t } = useI18n();
  const source = useDataSource();
  const { data, errorKey } = useLoad(target === null ? null : JSON.stringify(target), () => {
    if (target === null) {
      return Promise.reject(new Error("kein Ziel"));
    }
    return target.kind === "object"
      ? source.getObjectXml(target.objectId)
      : source.getXmlAt(target.datasetId, target.file, target.line, target.column);
  });
  if (target === null) {
    return <p className="hint">{t("xml.empty")}</p>;
  }
  if (errorKey !== null) {
    return <p role="alert">{t(errorKey)}</p>;
  }
  if (data === null) {
    return <p>{t("app.loading")}</p>;
  }
  return <XmlView window={data} colors={colors} />;
}
