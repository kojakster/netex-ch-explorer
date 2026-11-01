// E2E-Pfad (Plan Abschnitt 11): Beispiel 01 laden, Fahrt öffnen, Halt anklicken; die richtige
// XML-Stelle und der richtige Frame müssen erscheinen. Die Auswahl läuft über CSS-Klassen, damit
// der Test nicht an Oberflächentexten hängt; der Dateiname und der Haltname sind Daten des Guides.

import { expect, test } from "@playwright/test";
import { frameBackground, guideAvailable, REQUIRE_GUIDE_ENV, toRgb } from "./support";

const GUIDE_READY_TIMEOUT_MS = 120_000;
const EXAMPLE_FILE = "01_NeTEx_Spiez_Interlaken_Ost.xml";
const STOP_NAME = "Interlaken West";
const STOP_XML = `<Name lang="de">${STOP_NAME}</Name>`;
const STOP_FRAME = "ServiceFrame";
const STOP_OBJECT_TYPE = "ScheduledStopPoint";

test.beforeEach(() => {
  if (guideAvailable()) {
    return;
  }
  const message = "Guide-Klon fehlt (siehe README, Schritt 3)";
  // Wie bei den pytest-Tests: mit NETEX_REQUIRE_GUIDE=1 ist ein fehlender Guide ein Fehler.
  expect(process.env[REQUIRE_GUIDE_ENV], message).not.toBe("1");
  test.skip(true, message);
});

test("Beispiel 01: Halt anklicken führt zur richtigen XML-Stelle und zum richtigen Frame", async ({
  page,
}) => {
  const problems: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error" || message.type() === "warning") {
      problems.push(`${message.type()}: ${message.text()}`);
    }
  });
  page.on("pageerror", (error) => problems.push(String(error)));

  // XSD laden und Beispiele prüfen dauert rund 20 s; erst danach ist die Prüfung bereit.
  await expect
    .poll(async () => (await page.request.get("/api/guide")).json(), {
      timeout: GUIDE_READY_TIMEOUT_MS,
    })
    .toMatchObject({ examplesReady: true });

  await page.goto("/");
  await page.getByText(EXAMPLE_FILE, { exact: true }).click();

  // Fahrt öffnen (Liste links, eine Fahrt pro Zeile)
  await page.locator(".journey-item").first().click();
  await expect(page.locator(".journey-view")).toBeVisible();

  // Die rechte Spalte erscheint erst, wenn eine Angabe gewählt ist.
  await expect(page.locator(".xml-column")).toHaveCount(0);

  // Halt anklicken
  await page.locator(".stop-table").getByText(STOP_NAME, { exact: true }).first().click();

  // Richtige XML-Stelle: markiert ist der Name des Haltepunkts.
  await expect(page.locator(".cm-focus").first()).toHaveText(STOP_XML);

  // Richtiger Frame: Randbeschriftung im XML und erstes Glied der Herkunftskette.
  await expect(
    page.locator(".cm-frame-label").filter({ hasText: STOP_FRAME }).first(),
  ).toBeVisible();
  const chain = page.locator(".provenance .chain-box");
  await expect(chain.first()).toContainText(STOP_FRAME);
  await expect(chain.nth(1)).toContainText(STOP_OBJECT_TYPE);
  await expect(chain.first()).toHaveCSS("background-color", toRgb(frameBackground(STOP_FRAME)));

  expect(problems).toEqual([]);
});
