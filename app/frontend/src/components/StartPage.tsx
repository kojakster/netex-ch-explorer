import { useI18n } from "../i18n";
import type { ExampleInfo } from "../types";
import { ExampleList } from "./ExampleList";

interface StartPageProps {
  examples: readonly ExampleInfo[];
  onOpenExample: (name: string) => void;
}

/** Startseite ohne Datensatz: kurze Anleitung in drei Schritten und die Beispiele des Guides. */
export function StartPage({ examples, onOpenExample }: StartPageProps) {
  const { t } = useI18n();
  return (
    <section className="start" aria-label={t("start.title")}>
      <h2>{t("start.title")}</h2>
      <ol className="start-steps">
        <li>{t("start.step1")}</li>
        <li>{t("start.step2")}</li>
        <li>{t("start.step3")}</li>
      </ol>
      <ExampleList examples={examples} selected={null} onOpen={onOpenExample} />
    </section>
  );
}
