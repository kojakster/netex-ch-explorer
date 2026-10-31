import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { DATASET, VALIDATED_DATASET } from "../testData";
import type { DatasetInfo, Detection } from "../types";
import { DatasetPanel } from "./DatasetPanel";

const DETECTION_110: Detection = {
  status: "detected",
  profile: "netex_1_10",
  reasons: [
    { evidence: "netex_1_10", key: "version.attribute_110", params: { version: "1.10" } },
    { evidence: "neutral", key: "version.namespace", params: { namespace: "urn:x" } },
  ],
};

function withDetection(detection: Detection | null): DatasetInfo {
  const [file] = DATASET.files;
  return { ...DATASET, files: file ? [{ ...file, detection }] : [] };
}

function renderPanel(dataset: DatasetInfo, props: { validating?: boolean; error?: string } = {}) {
  const onValidate = vi.fn();
  render(
    <DatasetPanel
      dataset={dataset}
      validating={props.validating ?? false}
      validationErrorKey={props.error ?? null}
      onValidate={onValidate}
    />,
  );
  return onValidate;
}

describe("DatasetPanel", () => {
  it("zeigt die erkannte Version mit Begründung und startet die Prüfung", () => {
    const onValidate = renderPanel(DATASET);
    expect(screen.getByText("Erkannt: CH-Profil 2.0 (Entwurf)")).toBeTruthy();
    expect(screen.getByText(/version="2.1"/)).toBeTruthy();
    expect(screen.getAllByText("spricht für CH 2.0").length).toBe(2);
    expect(screen.getByText("Noch nicht geprüft.")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Prüfen" }));
    expect(onValidate).toHaveBeenCalledWith(false);
    expect(screen.queryByRole("button", { name: "Trotzdem als CH 2.0 prüfen" })).toBeNull();
  });

  it("prüft eine 1.10-Datei nicht und sagt das", () => {
    renderPanel(withDetection(DETECTION_110));
    expect(screen.getByText("Erkannt: NeTEx 1.10")).toBeTruthy();
    expect(screen.getByText(/Diese Datei wird nicht gegen CH 2.0 geprüft/)).toBeTruthy();
    expect((screen.getByRole("button", { name: "Prüfen" }) as HTMLButtonElement).disabled).toBe(
      true,
    );
    expect(screen.getByText(/Keine Datei ist als CH 2.0 erkannt/)).toBeTruthy();
    expect(screen.getByText(/version="1.10"/)).toBeTruthy();
  });

  it("zeigt mehrdeutige und unbekannte Versionen", () => {
    renderPanel(withDetection({ status: "ambiguous", profile: null, reasons: [] }));
    expect(screen.getByText("Version mehrdeutig")).toBeTruthy();
  });

  it.each(["ambiguous", "unknown"] as const)(
    "bietet bei Version %s den Knopf „Trotzdem als CH 2.0 prüfen“ an",
    (status) => {
      const onValidate = renderPanel(withDetection({ status, profile: null, reasons: [] }));
      expect((screen.getByRole("button", { name: "Prüfen" }) as HTMLButtonElement).disabled).toBe(
        true,
      );
      fireEvent.click(screen.getByRole("button", { name: "Trotzdem als CH 2.0 prüfen" }));
      expect(onValidate).toHaveBeenCalledWith(true);
      expect(screen.getByText(/nie so geprüft/)).toBeTruthy();
    },
  );

  it("bietet den Knopf bei erkannter 1.10-Datei und bei nicht lesbarer Datei nicht an", () => {
    renderPanel(withDetection(DETECTION_110));
    expect(screen.queryByRole("button", { name: "Trotzdem als CH 2.0 prüfen" })).toBeNull();
    cleanup();
    const [file] = DATASET.files;
    renderPanel({
      ...DATASET,
      files: file
        ? [
            {
              ...file,
              readable: false,
              detection: { status: "unknown", profile: null, reasons: [] },
            },
          ]
        : [],
    });
    expect(screen.queryByRole("button", { name: "Trotzdem als CH 2.0 prüfen" })).toBeNull();
  });

  it("sperrt den Knopf „Trotzdem …“ während der Prüfung", () => {
    renderPanel(withDetection({ status: "unknown", profile: null, reasons: [] }), {
      validating: true,
    });
    expect(
      (screen.getByRole("button", { name: "Trotzdem als CH 2.0 prüfen" }) as HTMLButtonElement)
        .disabled,
    ).toBe(true);
  });

  it("vermerkt sichtbar, dass auf Wunsch als CH 2.0 geprüft wurde", () => {
    renderPanel({
      ...VALIDATED_DATASET,
      validation: {
        ...(VALIDATED_DATASET.validation as NonNullable<DatasetInfo["validation"]>),
        forced: true,
        files: [
          {
            fileId: 1,
            checked: true,
            forced: true,
            reason: { severity: "info", key: "validation.forced", params: {} },
          },
        ],
      },
    });
    expect(screen.getByText("Als CH 2.0 geprüft auf Wunsch, Version nicht erkannt.")).toBeTruthy();
  });

  it("markiert eine nicht lesbare Datei", () => {
    const [file] = DATASET.files;
    renderPanel({ ...DATASET, files: file ? [{ ...file, readable: false }] : [] });
    expect(screen.getByText("nicht lesbar")).toBeTruthy();
  });

  it("kennzeichnet einen Eintrag ohne Inhalt (abgewiesene Datei, Archiv) anders als eine kaputte Datei", () => {
    const [file] = DATASET.files;
    renderPanel({
      ...DATASET,
      files: file ? [{ ...file, readable: false, size: 0, elements: 0, detection: null }] : [],
    });
    expect(screen.getByText("keine XML-Datei (siehe Diagnosen)")).toBeTruthy();
  });

  it("zeigt das Ergebnis als „geprüft gegen Entwurf“, nie als „gültig“", () => {
    renderPanel(VALIDATED_DATASET);
    expect(screen.getByText("Geprüft gegen Entwurf b7ac158")).toBeTruthy();
    expect(
      screen.getByText(
        "Schweizer Kernregeln für den Fahrplan geprüft; übrige Profilregeln noch nicht eingebunden.",
      ),
    ).toBeTruthy();
    expect(screen.getAllByText(/durchgeführt/).length).toBe(3);
    expect(screen.queryByText(/gültig/i)).toBeNull();
  });

  it("nennt nicht durchgeführte Schritte und nicht geprüfte Dateien mit Grund", () => {
    renderPanel({
      ...VALIDATED_DATASET,
      validation: {
        guideCommit: null,
        forced: false,
        steps: [
          {
            id: "xsd",
            performed: false,
            reason: {
              severity: "warning",
              key: "validation.step_unavailable",
              params: { step: "xsd" },
            },
          },
        ],
        files: [
          {
            fileId: 1,
            checked: false,
            forced: false,
            reason: { severity: "info", key: "validation.file_skipped_profile", params: {} },
          },
          { fileId: 9, checked: false, forced: false, reason: null },
        ],
      },
    });
    expect(screen.getByText("Geprüft gegen Entwurf unbekannt")).toBeTruthy();
    expect(screen.getByText(/Der Prüfschritt xsd konnte nicht durchgeführt werden/)).toBeTruthy();
    expect(screen.getByText(/ch20_three_stops.xml: nicht geprüft/)).toBeTruthy();
    expect(screen.getByText(/^9: nicht geprüft/)).toBeTruthy();
  });

  it("zeigt den Lauf und Fehler der Prüfung", () => {
    renderPanel(DATASET, { validating: true, error: "error.internal" });
    expect(screen.getByRole("button", { name: "Prüfung läuft …" })).toBeTruthy();
    expect(screen.getByRole("alert").textContent).toContain("Interner Fehler");
  });
});
