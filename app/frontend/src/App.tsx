import { type CSSProperties, useEffect, useMemo, useRef, useState } from "react";
import { ApiError, type DataSource } from "./api";
import {
  columnLayout,
  DETAILS_LIMITS,
  DETAILS_STORAGE_KEY,
  SIDEBAR_LIMITS,
  SIDEBAR_STORAGE_KEY,
  useStoredWidth,
  useViewportWidth,
} from "./columnResize";
import { CalculationChain } from "./components/CalculationChain";
import { DatasetPanel } from "./components/DatasetPanel";
import { DatasetPicker } from "./components/DatasetPicker";
import { DiagnosticList } from "./components/DiagnosticList";
import { FrameLegend } from "./components/FrameLegend";
import { GuideStatusBox } from "./components/GuideStatusBox";
import { HelpPage } from "./components/HelpPage";
import { JourneyList } from "./components/JourneyList";
import { JourneyView } from "./components/JourneyView";
import { LanguageSwitch } from "./components/LanguageSwitch";
import { ObjectTree } from "./components/ObjectTree";
import { ObjectView } from "./components/ObjectView";
import { ProvenanceChain } from "./components/ProvenanceChain";
import { ResizeHandle } from "./components/ResizeHandle";
import { type SidebarTab, SidebarTabs } from "./components/SidebarTabs";
import { StartPage } from "./components/StartPage";
import { XmlPanel, type XmlTarget } from "./components/XmlPanel";
import { DataSourceContext, LOAD_ERROR_KEY, useLoad } from "./data";
import {
  type CenterView,
  canGoBack,
  canGoForward,
  currentSelection,
  EMPTY_HISTORY,
  goBack,
  goForward,
  visit,
} from "./history";
import { DEFAULT_LANGUAGE, I18nContext, messagesFor, translate } from "./i18n";
import type {
  AppInfo,
  ChainLink,
  DatasetInfo,
  DiagnosticInfo,
  GuideInfo,
  StopInfo,
  TimeInfo,
} from "./types";

type View = "main" | "help";

// Abstand der Nachfragen, solange die Beispiele noch geprüft werden (die XSD wird geladen).
const GUIDE_POLL_MS = 2000;
// So viele Nachfragen in Folge dürfen fehlschlagen, bevor die Oberfläche den Fehler anzeigt.
const GUIDE_POLL_MAX_FAILURES = 5;

interface AppProps {
  dataSource: DataSource;
}

/** Anzahl aller Befunde der Prüfung (alle Schweregrade). */
function findingCount(dataset: DatasetInfo): number {
  const counts = dataset.diagnosticCounts;
  return counts.error + counts.warning + counts.info;
}

function errorKeyOf(error: unknown): string {
  return error instanceof ApiError ? error.key : LOAD_ERROR_KEY;
}

export function App({ dataSource }: AppProps) {
  const [appInfo, setAppInfo] = useState<AppInfo | null>(null);
  const [guide, setGuide] = useState<GuideInfo | null>(null);
  const [errorKey, setErrorKey] = useState<string | null>(null);
  const [language, setLanguage] = useState(DEFAULT_LANGUAGE);
  const [view, setView] = useState<View>("main");
  // Name des geöffneten Beispiels; eigene Dateien haben keinen Namen in der Beispielliste.
  const [exampleName, setExampleName] = useState<string | null>(null);
  const [opening, setOpening] = useState(false);
  const [dataset, setDataset] = useState<DatasetInfo | null>(null);
  const [datasetErrorKey, setDatasetErrorKey] = useState<string | null>(null);
  // Eine Validierung gehört zu dem Datensatz, für den sie gestartet wurde (ID), nie zu einem späteren.
  const [validatingId, setValidatingId] = useState<string | null>(null);
  const [validationError, setValidationError] = useState<{ id: string; key: string } | null>(null);
  // Zählt die abgeschlossenen Validierungen des offenen Datensatzes (Schlüssel für die Diagnosen).
  const [validationRuns, setValidationRuns] = useState(0);
  const [history, setHistory] = useState(EMPTY_HISTORY);
  // Schalter „Herkunft zeigen“ der Fahrtansicht; er bleibt beim Wechsel zwischen Fahrten.
  const [showOrigin, setShowOrigin] = useState(false);
  const [sidebarTab, setSidebarTab] = useState<SidebarTab>("journeys");
  // Die rechte Spalte (Rechenkette, Herkunft, XML) erscheint erst, wenn etwas gewählt ist.
  const [detailsOpen, setDetailsOpen] = useState(false);
  // Stelle einer Diagnose; ersetzt die Markierung der Auswahl, bis wieder etwas gewählt wird.
  const [positionTarget, setPositionTarget] = useState<XmlTarget | null>(null);
  const selection = currentSelection(history);
  const settingsIssues = appInfo?.issues ?? [];
  const objectId = selection?.objectId ?? null;
  const selectedElement = selection?.elementId ?? null;
  const xmlTarget: XmlTarget | null =
    positionTarget ??
    (selectedElement === null ? null : { kind: "object", objectId: selectedElement });
  // Nur die Antwort der zuletzt gestarteten Öffnung zählt (schnelles Umschalten).
  const openRequest = useRef(0);
  // Die Fahrten der Datei: Sie bestimmen, ob die Mitte zwischen „Fahrt“ und „Objekt“ umschaltet.
  const datasetId = dataset?.id ?? null;
  const journeys = useLoad(datasetId, () => dataSource.getJourneys(datasetId ?? ""));
  const isJourney = journeys.data?.some((item) => item.object.id === objectId) ?? false;
  const showDetails = detailsOpen && (selection !== null || positionTarget !== null);
  const [storedSidebar, setSidebarWidth, resetSidebarWidth] = useStoredWidth(
    SIDEBAR_STORAGE_KEY,
    SIDEBAR_LIMITS,
  );
  const [storedDetails, setDetailsWidth, resetDetailsWidth] = useStoredWidth(
    DETAILS_STORAGE_KEY,
    DETAILS_LIMITS,
  );
  const columns = columnLayout(
    useViewportWidth(),
    dataset !== null,
    showDetails,
    storedSidebar,
    storedDetails,
  );
  const columnWidths = {
    "--sidebar-width": `${columns.sidebar.width}px`,
    "--details-width": `${columns.details.width}px`,
  } as CSSProperties;
  const centerView: CenterView = selection?.view ?? "object";
  const journeyKey = centerView === "journey" ? objectId : null;
  const journeyLoad = useLoad(journeyKey, () => dataSource.getJourney(journeyKey ?? ""));

  useEffect(() => {
    let active = true;
    Promise.all([dataSource.getAppInfo(), dataSource.getGuide()])
      .then(([info, guideInfo]) => {
        if (active) {
          setAppInfo(info);
          setGuide(guideInfo);
          setLanguage(info.language);
        }
      })
      .catch((error: unknown) => {
        if (active) {
          setErrorKey(errorKeyOf(error));
        }
      });
    return () => {
      active = false;
    };
  }, [dataSource]);

  // Solange die Beispiele geprüft werden, fragt die Oberfläche den Stand regelmässig nach. Ein
  // einzelner Fehler beendet das Nachfragen nicht; erst mehrere in Folge zeigen den Fehler.
  useEffect(() => {
    if (guide === null || guide.examplesReady) {
      return;
    }
    let active = true;
    let failures = 0;
    let timer = 0;
    const poll = () => {
      timer = window.setTimeout(() => {
        dataSource
          .getGuide()
          .then((next) => {
            if (active) {
              setGuide(next);
            }
          })
          .catch((error: unknown) => {
            if (!active) {
              return;
            }
            failures += 1;
            if (failures >= GUIDE_POLL_MAX_FAILURES) {
              setErrorKey(errorKeyOf(error));
            } else {
              poll();
            }
          });
      }, GUIDE_POLL_MS);
    };
    poll();
    return () => {
      active = false;
      window.clearTimeout(timer);
    };
  }, [guide, dataSource]);

  const i18n = useMemo(() => {
    const messages = messagesFor(language);
    return {
      language,
      t: (key: string, params?: Readonly<Record<string, string | number>>) =>
        translate(messages, key, params),
    };
  }, [language]);
  const { t } = i18n;

  useEffect(() => {
    document.documentElement.lang = language;
  }, [language]);

  /** Schliesst den bisherigen Datensatz auf dem Server (löscht seine Dateien in work/). */
  const closeDataset = (id: string) => {
    dataSource.closeDataset(id).catch(() => undefined);
  };

  const openDataset = (open: () => Promise<DatasetInfo>, name: string | null) => {
    if (dataset !== null) {
      closeDataset(dataset.id);
    }
    setExampleName(name);
    setOpening(true);
    setDataset(null);
    setDatasetErrorKey(null);
    setValidationError(null);
    setValidationRuns(0);
    setHistory(EMPTY_HISTORY);
    setPositionTarget(null);
    setDetailsOpen(false);
    setSidebarTab("journeys");
    setView("main");
    openRequest.current += 1;
    const request = openRequest.current;
    open()
      .then((opened) => {
        if (request === openRequest.current) {
          setDataset(opened);
          setOpening(false);
        } else {
          closeDataset(opened.id);
        }
      })
      .catch((error: unknown) => {
        if (request === openRequest.current) {
          setDatasetErrorKey(errorKeyOf(error));
          setOpening(false);
        }
      });
  };

  const openExample = (name: string) => openDataset(() => dataSource.openExample(name), name);

  const openFiles = (files: File[]) => openDataset(() => dataSource.openFiles(files), null);

  const validate = (forceCh20: boolean) => {
    if (dataset === null) {
      return;
    }
    const id = dataset.id;
    const request = openRequest.current;
    // Ergebnis und Fehler gelten nur, solange derselbe Datensatz offen ist.
    const stillOpen = () => request === openRequest.current;
    setValidatingId(id);
    setValidationError(null);
    dataSource
      .validate(id, forceCh20)
      .then((validated) => {
        if (stillOpen()) {
          setDataset(validated);
          setValidationRuns((runs) => runs + 1);
        }
      })
      .catch((error: unknown) => {
        if (stillOpen()) {
          setValidationError({ id, key: errorKeyOf(error) });
          setValidationRuns((runs) => runs + 1);
        }
      })
      .finally(() => setValidatingId((current) => (current === id ? null : current)));
  };

  /** Zeigt ein Objekt oder eine Fahrt und markiert darin eine Angabe (Standard: das Objekt selbst). */
  const navigate = (
    id: string,
    elementId: string = id,
    view: CenterView = "object",
    timeId: string | null = null,
  ) => {
    setPositionTarget(null);
    setDetailsOpen(true);
    setHistory((previous) => visit(previous, { objectId: id, elementId, view, timeId }));
  };

  const selectObject = (id: string) => navigate(id);

  /** Öffnet die Fahrt aus der Liste: ruhige Fahrplanansicht, die rechte Spalte bleibt zu. */
  const openJourney = (id: string) => {
    navigate(id, id, "journey");
    setDetailsOpen(false);
  };

  /** Hebt die Auswahl auf: die rechte Spalte verschwindet, der Hauptbereich wird breiter. */
  const closeDetails = () => {
    setPositionTarget(null);
    setDetailsOpen(false);
  };

  /** Wählt eine Angabe in der Fahrtansicht; die Rechenkette einer Zeit bleibt nicht stehen. */
  const selectJourneyElement = (elementId: string) => {
    if (objectId !== null) {
      navigate(objectId, elementId, "journey");
    }
  };

  /** Wählt einen Summanden der Rechenkette; die Rechenkette bleibt stehen. */
  const selectCalculationElement = (elementId: string) => {
    if (objectId !== null) {
      navigate(objectId, elementId, "journey", selection?.timeId ?? null);
    }
  };

  /** Wählt eine Zeit der Fahrtansicht: Rechenkette rechts, XML-Markierung auf ihrer Quelle. */
  const selectTime = (time: TimeInfo, stop: StopInfo) => {
    if (objectId !== null) {
      const source = time.source ?? time.reason?.element ?? stop.point;
      navigate(objectId, source.id, "journey", time.id);
    }
  };

  const switchView = (view: CenterView) => {
    if (objectId !== null) {
      navigate(objectId, objectId, view);
    }
  };

  const selectElement = (id: string) => {
    if (objectId !== null) {
      navigate(
        objectId,
        id,
        centerView,
        centerView === "journey" ? (selection?.timeId ?? null) : null,
      );
    }
  };

  const selectLink = (link: ChainLink) => {
    if (link.kind === "element") {
      selectElement(link.object.id);
    } else {
      navigate(link.object.id);
    }
  };

  const stepHistory = (step: typeof goBack) => {
    setPositionTarget(null);
    setHistory(step);
  };

  const showDiagnostic = (diagnostic: DiagnosticInfo) => {
    if (dataset !== null && diagnostic.line !== null) {
      setDetailsOpen(true);
      setPositionTarget({
        kind: "position",
        datasetId: dataset.id,
        file: diagnostic.fileId,
        line: diagnostic.line,
        column: diagnostic.column ?? 1,
      });
    }
  };

  return (
    <DataSourceContext.Provider value={dataSource}>
      <I18nContext.Provider value={i18n}>
        <div className="app">
          <header className="app-header">
            <h1>{t("app.title")}</h1>
            {appInfo !== null && guide !== null && (
              <DatasetPicker
                examples={guide.examples}
                selected={exampleName}
                onOpenExample={openExample}
                onOpenFiles={openFiles}
              />
            )}
            <nav>
              {guide !== null && <GuideStatusBox guide={guide} settingsIssues={settingsIssues} />}
              {appInfo && <LanguageSwitch languages={appInfo.languages} onChange={setLanguage} />}
              <button type="button" onClick={() => setView("help")} disabled={appInfo === null}>
                {t("app.help")}
              </button>
            </nav>
          </header>
          {errorKey !== null && (
            <p className="load-error" role="alert">
              {t(errorKey)}
            </p>
          )}
          {errorKey === null && appInfo === null && <p className="page-note">{t("app.loading")}</p>}
          {appInfo !== null && view === "help" && (
            <HelpPage appInfo={appInfo} guide={guide} onBack={() => setView("main")} />
          )}
          {appInfo !== null && view === "main" && (
            <div
              className={`layout${dataset === null ? " layout-start" : ""}${showDetails ? " layout-details" : ""}`}
              style={columnWidths}
            >
              {dataset !== null && (
                <aside className="sidebar">
                  <SidebarTabs
                    active={sidebarTab}
                    onChange={setSidebarTab}
                    findingCount={dataset.validation === null ? null : findingCount(dataset)}
                  >
                    {sidebarTab === "journeys" && (
                      <JourneyList
                        journeys={journeys.data}
                        errorKey={journeys.errorKey}
                        selected={centerView === "journey" ? objectId : null}
                        onOpenJourney={openJourney}
                      />
                    )}
                    {sidebarTab === "objects" && (
                      <ObjectTree
                        dataset={dataset}
                        colors={appInfo.frameColors}
                        onSelect={selectObject}
                      />
                    )}
                    {sidebarTab === "check" && (
                      <>
                        <DatasetPanel
                          dataset={dataset}
                          validating={validatingId === dataset.id}
                          validationErrorKey={
                            validationError?.id === dataset.id ? validationError.key : null
                          }
                          onValidate={validate}
                        />
                        <DiagnosticList
                          datasetId={dataset.id}
                          refreshKey={`run${validationRuns}`}
                          onShow={showDiagnostic}
                        />
                      </>
                    )}
                  </SidebarTabs>
                </aside>
              )}
              {dataset !== null && columns.sidebar.handle && (
                <ResizeHandle
                  labelKey="resize.sidebar"
                  width={columns.sidebar.width}
                  min={SIDEBAR_LIMITS.min}
                  max={columns.sidebar.max}
                  columnOnLeft
                  onChange={setSidebarWidth}
                  onReset={resetSidebarWidth}
                />
              )}
              <main className="content">
                {datasetErrorKey !== null && <p role="alert">{t(datasetErrorKey)}</p>}
                {opening && datasetErrorKey === null && <p>{t("app.loading")}</p>}
                {dataset === null && !opening && guide !== null && (
                  <StartPage examples={guide.examples} onOpenExample={openExample} />
                )}
                {dataset !== null && objectId === null && (
                  <p className="hint">{t("app.selectObject")}</p>
                )}
                {objectId !== null && (
                  <>
                    <div className="content-bar">
                      <nav className="history" aria-label={t("feature.navigation_history.title")}>
                        <button
                          type="button"
                          onClick={() => stepHistory(goBack)}
                          disabled={!canGoBack(history)}
                        >
                          ← {t("nav.back")}
                        </button>
                        <button
                          type="button"
                          onClick={() => stepHistory(goForward)}
                          disabled={!canGoForward(history)}
                        >
                          {t("nav.forward")} →
                        </button>
                      </nav>
                      {isJourney && (
                        <nav className="view-tabs" aria-label={t("view.title")}>
                          <button
                            type="button"
                            aria-pressed={centerView === "journey"}
                            onClick={() => switchView("journey")}
                          >
                            {t("view.journey")}
                          </button>
                          <button
                            type="button"
                            aria-pressed={centerView === "object"}
                            onClick={() => switchView("object")}
                          >
                            {t("view.object")}
                          </button>
                        </nav>
                      )}
                    </div>
                    {centerView === "journey" && journeyLoad.errorKey !== null && (
                      <p role="alert">{t(journeyLoad.errorKey)}</p>
                    )}
                    {centerView === "journey" &&
                      journeyLoad.data === null &&
                      journeyLoad.loading && <p>{t("app.loading")}</p>}
                    {centerView === "journey" && journeyLoad.data !== null && (
                      <JourneyView
                        journey={journeyLoad.data}
                        colors={appInfo.frameColors}
                        selected={showDetails && positionTarget === null ? selectedElement : null}
                        selectedTime={showDetails ? (selection?.timeId ?? null) : null}
                        onSelect={selectJourneyElement}
                        onSelectTime={selectTime}
                        onShowDiagnostic={showDiagnostic}
                        showOrigin={showOrigin}
                        onShowOriginChange={setShowOrigin}
                      />
                    )}
                    {centerView === "object" && (
                      <ObjectView
                        objectId={objectId}
                        colors={appInfo.frameColors}
                        selectedElement={showDetails ? selectedElement : null}
                        onSelectElement={selectElement}
                        onNavigate={navigate}
                      />
                    )}
                  </>
                )}
              </main>
              {showDetails && columns.details.handle && (
                <ResizeHandle
                  labelKey="resize.details"
                  width={columns.details.width}
                  min={DETAILS_LIMITS.min}
                  max={columns.details.max}
                  columnOnLeft={false}
                  onChange={setDetailsWidth}
                  onReset={resetDetailsWidth}
                />
              )}
              {showDetails && (
                <aside className="xml-column" aria-label={t("details.title")}>
                  <div className="details-bar">
                    <h2>{t("details.title")}</h2>
                    <button type="button" onClick={closeDetails}>
                      {t("details.close")}
                    </button>
                  </div>
                  {positionTarget === null &&
                    selection?.timeId != null &&
                    journeyLoad.data !== null && (
                      <CalculationChain
                        journey={journeyLoad.data}
                        timeId={selection.timeId}
                        colors={appInfo.frameColors}
                        selected={selectedElement}
                        onSelect={selectCalculationElement}
                      />
                    )}
                  <ProvenanceChain
                    elementId={positionTarget === null ? selectedElement : null}
                    colors={appInfo.frameColors}
                    onSelect={selectLink}
                  />
                  <XmlPanel target={xmlTarget} colors={appInfo.frameColors} />
                  <FrameLegend colors={appInfo.frameColors} onHelp={() => setView("help")} />
                </aside>
              )}
            </div>
          )}
        </div>
      </I18nContext.Provider>
    </DataSourceContext.Provider>
  );
}
