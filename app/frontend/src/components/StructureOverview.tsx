import { colorOf } from "../colors";
import { useI18n } from "../i18n";
import { buildStructure, type StructureBox, type StructureRow } from "../structure";
import type { JourneyViewInfo } from "../types";
import { FrameLegend } from "./FrameLegend";
import type { SourceProps } from "./sourceProps";

function Box({ box, colors, selected, onSelect }: SourceProps & { box: StructureBox }) {
  const { t } = useI18n();
  const { object, problem } = box;
  const lines = (
    <>
      {box.netex !== null && <span className="struct-name">{box.netex}</span>}
      {box.detail !== null && <code className="struct-detail">{box.detail}</code>}
      {box.text !== null && <span className="struct-text">{t(box.text.key, box.text.params)}</span>}
      {problem !== null && (
        <span className="struct-text">
          {t(problem === "absent" ? "structure.notInFile" : "structure.notFound")}
        </span>
      )}
      {object?.frame != null && <span className="struct-frame">{object.frame.name}</span>}
    </>
  );
  if (object === null) {
    // Fehlend oder abgeleitet: keine Stelle in der Datei, deshalb weder Farbe noch Klick.
    return (
      <div
        className={`struct-box ${problem === null ? "struct-derived" : "struct-missing"}`}
        title={problem === null ? undefined : t(`lookup.${problem}`, { ref: box.detail ?? "" })}
      >
        {lines}
      </div>
    );
  }
  const color = colorOf(object, colors);
  return (
    <button
      type="button"
      className={`struct-box struct-object${selected === object.id ? " selected" : ""}`}
      style={color === null ? undefined : { backgroundColor: color.background, color: color.text }}
      onClick={() => onSelect(object.id)}
    >
      {lines}
    </button>
  );
}

function Row({ row, ...source }: SourceProps & { row: StructureRow }) {
  const { t } = useI18n();
  return (
    <section className="struct-row" aria-label={t(`structure.${row.id}.title`)}>
      <h4>{t(`structure.${row.id}.title`)}</h4>
      <ol className="struct-steps">
        {row.steps.map((step) => (
          <li key={step.map((box) => box.id).join("|")} className="struct-step">
            <div className="struct-stack">
              {step.map((box) => (
                <Box key={box.id} box={box} {...source} />
              ))}
            </div>
          </li>
        ))}
      </ol>
      <p className="note">{t(`structure.${row.id}.explain`)}</p>
    </section>
  );
}

/** „Wie ist diese Fahrt aufgebaut?“: Boxen in der Farbe ihres Frames, anklickbar, mit Erklärsatz. */
export function StructureOverview({
  journey,
  ...source
}: SourceProps & { journey: JourneyViewInfo }) {
  const { t } = useI18n();
  return (
    <details className="structure">
      <summary>{t("structure.title")}</summary>
      <p className="note">{t("structure.intro")}</p>
      <FrameLegend colors={source.colors} />
      {buildStructure(journey).map((row) => (
        <Row key={row.id} row={row} {...source} />
      ))}
    </details>
  );
}
