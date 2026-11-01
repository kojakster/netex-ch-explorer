import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { MESSAGES, messagesFor, translate } from "./i18n";
import { SEVERITY_SYMBOLS } from "./symbols";
import type { GuideTestState, Severity } from "./types";

const SRC = __dirname;

function sourceFiles(directory: string): string[] {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) {
      return sourceFiles(path);
    }
    return /\.tsx?$/.test(entry.name) && !/\.test\.tsx?$/.test(entry.name) ? [path] : [];
  });
}

describe("translate", () => {
  it("setzt Parameter ein", () => {
    expect(translate({ k: "{count} Blätter" }, "k", { count: 3 })).toBe("3 Blätter");
  });

  it("lässt unbekannte Platzhalter stehen", () => {
    expect(translate({ k: "a {x} b" }, "k")).toBe("a {x} b");
  });

  it("wählt bei count 1 den Einzahltext, sonst den Mehrzahltext", () => {
    const messages = { k: "{count} Tage", "k.one": "{count} Tag" };
    expect(translate(messages, "k", { count: 1 })).toBe("1 Tag");
    expect(translate(messages, "k", { count: "1" })).toBe("1 Tag");
    expect(translate(messages, "k", { count: 0 })).toBe("0 Tage");
    expect(translate(messages, "k", { count: 2 })).toBe("2 Tage");
    expect(translate(messages, "k", { count: "?" })).toBe("? Tage");
    expect(translate(messages, "k")).toBe("{count} Tage");
  });

  it("nimmt bei count 1 den Mehrzahltext, wenn es keinen Einzahltext gibt", () => {
    expect(translate({ k: "{count}×" }, "k", { count: 1 })).toBe("1×");
  });

  it("zeigt bei fehlendem Schlüssel den Schlüssel selbst", () => {
    expect(translate({}, "fehlt.ganz")).toBe("fehlt.ganz");
  });

  it("fällt bei unbekannter Sprache auf Deutsch zurück", () => {
    expect(messagesFor("xx")).toBe(MESSAGES["de-CH"]);
  });
});

describe("Sprachdateien", () => {
  const languages = Object.keys(MESSAGES);
  const reference = Object.keys(MESSAGES["de-CH"] ?? {}).sort();

  it("haben alle dieselben Schlüssel und keine leeren Texte", () => {
    for (const language of languages) {
      const messages = MESSAGES[language] ?? {};
      expect(Object.keys(messages).sort()).toEqual(reference);
      for (const value of Object.values(messages)) {
        expect(value.trim()).not.toBe("");
      }
    }
  });

  it("haben Einzahltexte nur zu vorhandenen Schlüsseln, gleich in allen Sprachen", () => {
    const singulars = reference.filter((key) => key.endsWith(".one"));
    expect(singulars.length).toBeGreaterThan(0);
    for (const key of singulars) {
      expect(reference, key).toContain(key.slice(0, -".one".length));
    }
  });

  it("nennen deutsche und englische Zähltexte Einzahl und Mehrzahl richtig", () => {
    const expected: Record<string, [string, string]> = {
      "de-CH": ["1 Betriebstag (1 Tag im Zeitraum)", "2 Betriebstage (7 Tage im Zeitraum)"],
      en: ["1 operating day (1 day in the period)", "2 operating days (7 days in the period)"],
    };
    for (const [language, [one, many]] of Object.entries(expected)) {
      const messages = messagesFor(language);
      const days = (count: number) => translate(messages, "unit.days", { count });
      expect(translate(messages, "header.days", { count: 1, period: days(1) })).toBe(one);
      expect(translate(messages, "header.days", { count: 2, period: days(7) })).toBe(many);
    }
  });

  it("enthalten jeden im Code verwendeten festen Schlüssel", () => {
    const used = new Set<string>();
    for (const file of sourceFiles(SRC)) {
      for (const match of readFileSync(file, "utf-8").matchAll(/\bt\("([^"]+)"/g)) {
        used.add(match[1] ?? "");
      }
    }
    expect(used.size).toBeGreaterThan(0);
    for (const key of used) {
      expect(reference, key).toContain(key);
    }
  });

  it("enthalten die zusammengesetzten Schlüssel der Oberfläche", () => {
    const severities: Severity[] = ["error", "warning", "info"];
    const testStates: GuideTestState[] = ["tested", "differs", "never_tested", "unknown"];
    const keys = [
      ...severities.flatMap((severity) => [
        `severity.${severity}`,
        `severity.${severity}.description`,
      ]),
      ...testStates.map((state) => `guide.testState.${state}`),
      ...languages.map((language) => `language.${language}`),
      ...["explicit", "default", "computed"].map((origin) => `time.offset.${origin}`),
      ...["both", "boardingOnly", "alightingOnly", "none", "unknown"].map(
        (access) => `stop.access.${access}`,
      ),
      ...["journey", "pattern", "stop", "journey_ref", "pattern_ref"].map(
        (scope) => `notice.scope.${scope}`,
      ),
      ...["arrival", "departure"].map((kind) => `calc.of.${kind}`),
      ...["explicit", "computed", "not_computable"].map((status) => `calc.status.${status}`),
      ...["departure_time", "day_offset", "run_time", "wait_time"].flatMap((step) => [
        `calc.step.${step}`,
        `calc.default.${step}`,
      ]),
      ...["journey", "line", "part"].map((role) => `journey.role.${role}`),
      "frame.unknown",
      "frame.notRelevant",
      "app.loadError",
    ];
    for (const key of keys) {
      expect(reference, key).toContain(key);
    }
    expect(Object.keys(SEVERITY_SYMBOLS).sort()).toEqual([...severities].sort());
  });
});
