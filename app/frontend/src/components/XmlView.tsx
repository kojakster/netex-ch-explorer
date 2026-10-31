import { EditorState } from "@codemirror/state";
import { EditorView } from "@codemirror/view";
import { useEffect, useRef } from "react";
import { useI18n } from "../i18n";
import type { FrameColor, XmlWindow } from "../types";
import { xmlExtensions } from "../xmlEditor";

interface XmlViewProps {
  window: XmlWindow;
  colors: readonly FrameColor[];
}

/** XML-Ausschnitt (nur lesen) mit exakter Markierung und farbigen Frame-Bereichen. */
export function XmlView({ window, colors }: XmlViewProps) {
  const { t } = useI18n();
  const host = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const element = host.current;
    if (element === null) {
      return;
    }
    // Shadow-DOM: CodeMirror setzt seine Stile dort ohne <style>-Element (strenge CSP).
    const root = element.shadowRoot ?? element.attachShadow({ mode: "open" });
    const view = new EditorView({
      root,
      parent: root,
      state: EditorState.create({ doc: window.text, extensions: xmlExtensions(window, colors) }),
    });
    view.dispatch({
      effects: EditorView.scrollIntoView(window.focusFrom, { y: "center" }),
    });
    return () => view.destroy();
  }, [window, colors]);
  return (
    <section className="xml-view" aria-label={t("xml.title")}>
      <h2>
        {t("xml.title")} <code>{window.fileName}</code>
      </h2>
      {window.truncated && <p className="note">{t("xml.truncated")}</p>}
      <div ref={host} className="xml-editor" />
    </section>
  );
}
