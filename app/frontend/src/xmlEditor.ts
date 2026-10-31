// CodeMirror-Erweiterungen für die XML-Ansicht: nur lesen, Zeilennummern der Datei,
// Frame-Bereiche farbig am Rand mit Frame-Name an der Startzeile, exakte Markierung.
// Alle Stile stehen im Theme (nicht in styles.css): Der Editor läuft in einem Shadow-DOM, damit
// CodeMirror seine Stile als Constructable Stylesheets setzt und die strenge CSP gilt.

import { xml } from "@codemirror/lang-xml";
import { defaultHighlightStyle, syntaxHighlighting } from "@codemirror/language";
import { EditorState, type Extension, RangeSetBuilder, StateField } from "@codemirror/state";
import {
  Decoration,
  type DecorationSet,
  EditorView,
  GutterMarker,
  gutter,
  lineNumbers,
  WidgetType,
} from "@codemirror/view";
import type { FrameBand, FrameColor, XmlWindow } from "./types";

/** Innerster Frame, der eine Zeile der Datei enthält (der zuletzt beginnende). */
export function frameForLine(frames: readonly FrameBand[], fileLine: number): FrameBand | null {
  let result: FrameBand | null = null;
  for (const band of frames) {
    if (band.fromLine <= fileLine && fileLine <= band.toLine) {
      if (result === null || band.fromLine >= result.fromLine) {
        result = band;
      }
    }
  }
  return result;
}

function colorOf(band: FrameBand, colors: readonly FrameColor[]): FrameColor | undefined {
  return colors.find((color) => color.key === band.colorKey);
}

class FrameMarker extends GutterMarker {
  constructor(
    readonly background: string,
    readonly label: string,
  ) {
    super();
  }

  override eq(other: GutterMarker): boolean {
    return (
      other instanceof FrameMarker &&
      other.background === this.background &&
      other.label === this.label
    );
  }

  override toDOM(): Node {
    const element = document.createElement("div");
    element.className = "cm-frame-marker";
    element.style.backgroundColor = this.background;
    element.title = this.label;
    return element;
  }
}

class FrameLabel extends WidgetType {
  constructor(
    readonly label: string,
    readonly color: FrameColor | undefined,
  ) {
    super();
  }

  override eq(other: FrameLabel): boolean {
    return other.label === this.label && other.color === this.color;
  }

  override toDOM(): HTMLElement {
    const element = document.createElement("div");
    element.className = "cm-frame-label";
    element.textContent = this.label;
    if (this.color !== undefined) {
      element.style.backgroundColor = this.color.background;
      element.style.color = this.color.text;
    }
    return element;
  }
}

function bandLabel(band: FrameBand): string {
  return band.xmlId === null ? band.name : `${band.name} ${band.xmlId}`;
}

function frameLabels(window: XmlWindow, colors: readonly FrameColor[]): Extension {
  return StateField.define<DecorationSet>({
    create(state) {
      const builder = new RangeSetBuilder<Decoration>();
      const starts = [...window.frames].sort((a, b) => a.fromLine - b.fromLine);
      for (const band of starts) {
        const docLine = band.fromLine - window.firstLine + 1;
        if (docLine >= 1 && docLine <= state.doc.lines) {
          const position = state.doc.line(docLine).from;
          builder.add(
            position,
            position,
            Decoration.widget({
              widget: new FrameLabel(bandLabel(band), colorOf(band, colors)),
              block: true,
              side: -1,
            }),
          );
        }
      }
      return builder.finish();
    },
    update(value) {
      return value;
    },
    provide: (field) => EditorView.decorations.from(field),
  });
}

function focusMark(window: XmlWindow): Extension {
  if (window.focusTo <= window.focusFrom) {
    return [];
  }
  const mark = Decoration.mark({ class: "cm-focus" }).range(window.focusFrom, window.focusTo);
  return EditorView.decorations.of(Decoration.set([mark]));
}

const xmlTheme = EditorView.theme({
  "&": { maxHeight: "80vh", fontSize: "13px" },
  ".cm-scroller": {
    overflow: "auto",
    fontFamily: 'ui-monospace, "SF Mono", Menlo, Consolas, monospace',
  },
  ".cm-frame-gutter": { width: "8px" },
  ".cm-frame-marker": { width: "6px", height: "100%" },
  ".cm-frame-label": {
    display: "inline-block",
    padding: "0 0.4rem",
    fontFamily: "system-ui, sans-serif",
    fontSize: "0.85em",
    fontWeight: "600",
    borderRadius: "2px",
  },
  ".cm-focus": { outline: "2px solid #000000", backgroundColor: "#fff3a0" },
});

/** Alle Erweiterungen für einen XML-Ausschnitt. */
export function xmlExtensions(window: XmlWindow, colors: readonly FrameColor[]): Extension[] {
  return [
    EditorState.readOnly.of(true),
    EditorView.editable.of(false),
    xmlTheme,
    lineNumbers({ formatNumber: (line) => String(line + window.firstLine - 1) }),
    gutter({
      class: "cm-frame-gutter",
      lineMarker(view, line) {
        const fileLine = view.state.doc.lineAt(line.from).number + window.firstLine - 1;
        const band = frameForLine(window.frames, fileLine);
        const color = band === null ? undefined : colorOf(band, colors);
        return band === null || color === undefined
          ? null
          : new FrameMarker(color.background, bandLabel(band));
      },
    }),
    xml(),
    syntaxHighlighting(defaultHighlightStyle),
    frameLabels(window, colors),
    focusMark(window),
  ];
}
