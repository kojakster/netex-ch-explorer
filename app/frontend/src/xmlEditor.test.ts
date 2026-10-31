import { EditorState } from "@codemirror/state";
import { EditorView } from "@codemirror/view";
import { XML } from "./testData";
import type { FrameBand } from "./types";
import { frameForLine, xmlExtensions } from "./xmlEditor";

function band(name: string, fromLine: number, toLine: number): FrameBand {
  return { objectId: name, name, xmlId: null, colorKey: name, fromLine, toLine };
}

describe("frameForLine", () => {
  const frames = [
    band("CompositeFrame", 1, 100),
    band("SiteFrame", 10, 20),
    band("ServiceFrame", 21, 90),
  ];

  it("wählt den innersten Frame", () => {
    expect(frameForLine(frames, 15)?.name).toBe("SiteFrame");
    expect(frameForLine(frames, 50)?.name).toBe("ServiceFrame");
    expect(frameForLine(frames, 95)?.name).toBe("CompositeFrame");
  });

  it("liefert null ausserhalb aller Frames", () => {
    expect(frameForLine(frames, 200)).toBeNull();
  });
});

describe("xmlExtensions", () => {
  it("markiert den Fokusbereich und beschriftet den Frame", () => {
    const parent = document.createElement("div");
    const view = new EditorView({
      parent,
      state: EditorState.create({
        doc: XML.text,
        extensions: xmlExtensions(XML, [
          { key: "TimetableFrame", background: "#0057B8", text: "#FFFFFF" },
        ]),
      }),
    });
    expect(parent.querySelector(".cm-focus")?.textContent).toContain("ServiceJourney");
    expect(parent.querySelector(".cm-frame-label")?.textContent).toBe(
      "TimetableFrame ch:1:TimetableFrame:SYN",
    );
    expect(parent.textContent).toContain("150");
    view.destroy();
  });
});
