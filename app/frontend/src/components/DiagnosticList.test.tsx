import { render, screen } from "@testing-library/react";
import type { DiagnosticInfo } from "../types";
import { DiagnosticItems, isSafeLink } from "./DiagnosticList";

const BASE: DiagnosticInfo = {
  category: "xsd",
  severity: "error",
  key: "xsd.violation",
  params: { detail: "<b>fett</b>" },
  fileId: 1,
  fileName: "a.xml",
  line: 3,
  column: 5,
  guideLink: null,
};

describe("DiagnosticItems", () => {
  it("zeigt Werte der Datei als Text, nie als HTML", () => {
    const { container } = render(<DiagnosticItems diagnostics={[BASE]} onShow={() => undefined} />);
    expect(screen.getByText("XSD: <b>fett</b>")).toBeTruthy();
    expect(container.querySelector("b")).toBeNull();
  });

  it("verlinkt nur https-Adressen", () => {
    const link = "https://github.com/openTdataCH/netexRealisationGuideSwitzerland/blob/x/src/a.md";
    expect(isSafeLink(link)).toBe(true);
    expect(isSafeLink("javascript:alert(1)")).toBe(false);
    expect(isSafeLink("http://example.org")).toBe(false);
    expect(isSafeLink(null)).toBe(false);
    render(
      <DiagnosticItems
        diagnostics={[{ ...BASE, guideLink: "javascript:alert(1)" }]}
        onShow={() => undefined}
      />,
    );
    expect(screen.queryByRole("link")).toBeNull();
  });
});
