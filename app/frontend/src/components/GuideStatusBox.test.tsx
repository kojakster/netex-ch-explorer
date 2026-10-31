import { render, screen } from "@testing-library/react";
import { GUIDE } from "../testData";
import { GuideStatusBox } from "./GuideStatusBox";

describe("GuideStatusBox", () => {
  it("zeigt Branch, kurzen Commit und getesteten Stand", () => {
    render(<GuideStatusBox guide={GUIDE} />);
    expect(screen.getByText("next")).toBeTruthy();
    expect(screen.getByText("b7ac158").getAttribute("title")).toBe(GUIDE.commit);
    expect(screen.getByText("73b337e")).toBeTruthy();
    expect(screen.getByText("mit diesem Stand getestet")).toBeTruthy();
    expect(screen.getByText("1 Blätter gelesen")).toBeTruthy();
  });

  it("meldet fehlende XSD und abweichenden Stand mit Symbol und Text", () => {
    render(
      <GuideStatusBox
        guide={{
          ...GUIDE,
          xsdPresent: false,
          xsdCommit: null,
          testState: "differs",
          issues: [
            {
              severity: "error",
              key: "guide.xsd_missing",
              params: { file: "xsd/xsd/NeTEx_publication.xsd", command: "git submodule update" },
            },
          ],
        }}
      />,
    );
    expect(screen.getByText("fehlt")).toBeTruthy();
    expect(screen.getByText("weicht vom zuletzt getesteten Stand ab")).toBeTruthy();
    expect(screen.getByText(/Im Guide-Ordner ausführen: git submodule update/)).toBeTruthy();
    expect(screen.getByText("Fehler")).toBeTruthy();
  });

  it("zeigt bei fehlendem Guide nur die Meldung", () => {
    render(
      <GuideStatusBox
        guide={{
          ...GUIDE,
          found: false,
          branch: null,
          commit: null,
          issues: [{ severity: "error", key: "guide.not_found", params: { path: "/x" } }],
        }}
      />,
    );
    expect(screen.queryByText("next")).toBeNull();
    expect(screen.getByText(/Kein Guide-Klon unter \/x/)).toBeTruthy();
  });

  it("zeigt, dass die XSD geladen wird und die Beispiele geprüft werden", () => {
    const { rerender } = render(
      <GuideStatusBox guide={{ ...GUIDE, examplesReady: false, xsdLoaded: false }} />,
    );
    expect(screen.getByText("XSD wird geladen …")).toBeTruthy();
    rerender(<GuideStatusBox guide={{ ...GUIDE, examplesReady: false, xsdLoaded: true }} />);
    expect(screen.getByText("Beispiele werden geprüft …")).toBeTruthy();
    rerender(<GuideStatusBox guide={GUIDE} />);
    expect(screen.getByText("bereit")).toBeTruthy();
  });

  it("zeigt keine Prüfung, wenn die XSD fehlt", () => {
    render(<GuideStatusBox guide={{ ...GUIDE, xsdPresent: false }} />);
    expect(screen.queryByText("bereit")).toBeNull();
  });
});
