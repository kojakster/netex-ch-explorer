// Prüftest: Oberflächentexte gehören in die Sprachdateien, nicht in den Code.

import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";

const LETTER = "A-Za-zÄÖÜäöüÀ-ÿ";
// Text zwischen JSX-Tags, der Buchstaben enthält. Einfache Näherung ohne Parser: Ein `>` nach
// `=` oder Leerraum (Pfeilfunktion, Vergleich) beginnt keinen JSX-Text, und Code-Zeichen
// beenden ihn.
const JSX_TEXT = new RegExp(`(?<![=\\s])>[^<>{}();=]*[${LETTER}][^<>{}();=]*<`);
// Feste Texte in Attributen, die Benutzer sehen.
const TEXT_ATTRIBUTE = new RegExp(
  `\\b(?:title|aria-label|placeholder|alt|label)="[^"]*[${LETTER}]`,
);

function tsxFiles(directory: string): string[] {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) {
      return tsxFiles(path);
    }
    return entry.name.endsWith(".tsx") && !entry.name.endsWith(".test.tsx") ? [path] : [];
  });
}

function withoutComments(source: string): string {
  return source.replace(/\/\*[\s\S]*?\*\//g, "").replace(/^\s*\/\/.*$/gm, "");
}

describe("keine festen Texte im Frontend-Code", () => {
  const files = tsxFiles(__dirname);

  it("findet Komponenten", () => {
    expect(files.length).toBeGreaterThan(0);
  });

  it.each(files)("%s", (file) => {
    const source = withoutComments(readFileSync(file, "utf-8"));
    expect(source).not.toMatch(JSX_TEXT);
    expect(source).not.toMatch(TEXT_ATTRIBUTE);
  });
});
