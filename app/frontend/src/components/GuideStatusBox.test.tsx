import { fireEvent, render, screen } from "@testing-library/react";
import { GUIDE } from "../testData";
import type { GuideInfo, Issue } from "../types";
import { GuideStatusBox, guideLevel } from "./GuideStatusBox";

function renderOpen(guide: GuideInfo, settingsIssues: Issue[] = []) {
  render(<GuideStatusBox guide={guide} settingsIssues={settingsIssues} />);
  fireEvent.click(screen.getByRole("button", { name: /^Guide:/ }));
}

const XSD_MISSING: Issue = {
  severity: "error",
  key: "guide.xsd_missing",
  params: { file: "xsd/xsd/NeTEx_publication.xsd", command: "git submodule update" },
};

describe("guideLevel", () => {
  it("ist ok bei getestetem Stand ohne Meldungen", () => {
    expect(guideLevel(GUIDE, [])).toBe("ok");
  });

  it("meldet eine Abweichung bei anderem Teststand oder bei Meldungen", () => {
    expect(guideLevel({ ...GUIDE, testState: "differs" }, [])).toBe("deviation");
    const note: Issue = { severity: "info", key: "guide.never_tested", params: { command: "x" } };
    expect(guideLevel(GUIDE, [note])).toBe("deviation");
  });

  it("meldet einen Fehler bei fehlendem Guide, fehlender XSD oder Fehlermeldung", () => {
    expect(guideLevel({ ...GUIDE, found: false }, [])).toBe("error");
    expect(guideLevel({ ...GUIDE, xsdPresent: false }, [])).toBe("error");
    expect(guideLevel(GUIDE, [XSD_MISSING])).toBe("error");
  });
});

describe("GuideStatusBox", () => {
  it("zeigt zunächst nur Punkt und Kurztext", () => {
    render(<GuideStatusBox guide={GUIDE} />);
    expect(screen.getByRole("button", { name: "Guide: ok" })).toBeTruthy();
    expect(screen.queryByText("next")).toBeNull();
  });

  it("klappt Branch, kurzen Commit und getesteten Stand per Klick auf und wieder zu", () => {
    renderOpen(GUIDE);
    expect(screen.getByText("next")).toBeTruthy();
    expect(screen.getByText("b7ac158").getAttribute("title")).toBe(GUIDE.commit);
    expect(screen.getByText("73b337e")).toBeTruthy();
    expect(screen.getByText("mit diesem Stand getestet")).toBeTruthy();
    expect(screen.getByText("1 Blatt gelesen")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Guide: ok" }));
    expect(screen.queryByText("next")).toBeNull();
  });

  it("meldet fehlende XSD und abweichenden Stand mit Symbol und Text", () => {
    renderOpen({
      ...GUIDE,
      xsdPresent: false,
      xsdCommit: null,
      testState: "differs",
      issues: [XSD_MISSING],
    });
    expect(screen.getByText("fehlt")).toBeTruthy();
    expect(screen.getByText("weicht vom zuletzt getesteten Stand ab")).toBeTruthy();
    expect(screen.getByText(/Im Guide-Ordner ausführen: git submodule update/)).toBeTruthy();
    expect(screen.getByText("Fehler")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Guide: Fehler" })).toBeTruthy();
  });

  it("zeigt bei fehlendem Guide nur die Meldung", () => {
    renderOpen({
      ...GUIDE,
      found: false,
      branch: null,
      commit: null,
      issues: [{ severity: "error", key: "guide.not_found", params: { path: "/x" } }],
    });
    expect(screen.queryByText("next")).toBeNull();
    expect(screen.getByText(/Kein Guide-Klon unter \/x/)).toBeTruthy();
  });

  it("zeigt Probleme der Einstellungen in den Details", () => {
    renderOpen(GUIDE, [
      { severity: "warning", key: "config.file_missing", params: { file: "config/settings.json" } },
    ]);
    expect(screen.getByText("Einstellungen")).toBeTruthy();
    expect(screen.getByText(/config\/settings.json fehlt/)).toBeTruthy();
  });

  it("zeigt, dass die XSD geladen wird und die Beispiele geprüft werden", () => {
    const { rerender } = render(
      <GuideStatusBox guide={{ ...GUIDE, examplesReady: false, xsdLoaded: false }} />,
    );
    fireEvent.click(screen.getByRole("button", { name: /^Guide:/ }));
    expect(screen.getByText("XSD wird geladen …")).toBeTruthy();
    rerender(<GuideStatusBox guide={{ ...GUIDE, examplesReady: false, xsdLoaded: true }} />);
    expect(screen.getByText("Beispiele werden geprüft …")).toBeTruthy();
    rerender(<GuideStatusBox guide={GUIDE} />);
    expect(screen.getByText("bereit")).toBeTruthy();
  });

  it("zeigt keine Prüfung, wenn die XSD fehlt", () => {
    renderOpen({ ...GUIDE, xsdPresent: false });
    expect(screen.queryByText("bereit")).toBeNull();
  });
});
