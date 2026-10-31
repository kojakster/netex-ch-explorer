import { useEffect, useMemo, useRef, useState } from "react";
import { ApiError, type DataSource } from "./api";
import { CalculationChain } from "./components/CalculationChain";
import { DiagnosticList } from "./components/DiagnosticList";
import { ExampleList } from "./components/ExampleList";
import { FrameLegend } from "./components/FrameLegend";
import { GuideStatusBox } from "./components/GuideStatusBox";
import { HelpPage } from "./components/HelpPage";
import { IssueList } from "./components/IssueList";
import { JourneyList } from "./components/JourneyList";
import { JourneyView } from "./components/JourneyView";
import { LanguageSwitch } from "./components/LanguageSwitch";
import { ObjectSearch } from "./components/ObjectSearch";
import { ObjectView } from "./components/ObjectView";
import { ProvenanceChain } from "./components/ProvenanceChain";
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

interface AppProps {
  dataSource: DataSource;
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
  const [exampleName, setExampleName] = useState<string | null>(null);
  const [dataset, setDataset] = useState<DatasetInfo | null>(null);
  const [datasetErrorKey, setDatasetErrorKey] = useState<string | null>(null);
  const [history, setHistory] = useState(EMPTY_HISTORY);
  // Stelle einer Diagnose; ersetzt die Markierung der Auswahl, bis wieder etwas gewählt wird.
  const [positionTarget, setPositionTarget] = useState<XmlTarget | null>(null);
  const selection = currentSelection(history);
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

  const openExample = (name: string) => {
    setExampleName(name);
    setDataset(null);
    setDatasetErrorKey(null);
    setHistory(EMPTY_HISTORY);
    setPositionTarget(null);
    openRequest.current += 1;
    const request = openRequest.current;
    dataSource
      .openExample(name)
      .then((opened) => {
        if (request === openRequest.current) {
          setDataset(opened);
        }
      })
      .catch((error: unknown) => {
        if (request === openRequest.current) {
          setDatasetErrorKey(errorKeyOf(error));
        }
      });
  };

  /** Zeigt ein Objekt oder eine Fahrt und markiert darin eine Angabe (Standard: das Objekt selbst). */
  const navigate = (
    id: string,
    elementId: string = id,
    view: CenterView = "object",
    timeId: string | null = null,
  ) => {
    setPositionTarget(null);
    setHistory((previous) => visit(previous, { objectId: id, elementId, view, timeId }));
  };

  const selectObject = (id: string) => navigate(id);

  const openJourney = (id: string) => navigate(id, id, "journey");

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
            <nav>
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
          {errorKey === null && appInfo === null && <p>{t("app.loading")}</p>}
          {appInfo !== null && view === "help" && (
            <HelpPage appInfo={appInfo} guide={guide} onBack={() => setView("main")} />
          )}
          {appInfo !== null && view === "main" && (
            <div className="layout">
              <aside className="sidebar">
                {guide !== null && <GuideStatusBox guide={guide} />}
                {appInfo.issues.length > 0 && (
                  <section className="settings-issues" aria-label={t("settings.title")}>
                    <h2>{t("settings.title")}</h2>
                    <IssueList issues={appInfo.issues} />
                  </section>
                )}
                <FrameLegend colors={appInfo.frameColors} onHelp={() => setView("help")} />
                {guide !== null && (
                  <ExampleList
                    examples={guide.examples}
                    selected={exampleName}
                    onOpen={openExample}
                  />
                )}
                {datasetErrorKey !== null && <p role="alert">{t(datasetErrorKey)}</p>}
                {exampleName !== null && dataset === null && datasetErrorKey === null && (
                  <p>{t("app.loading")}</p>
                )}
                {dataset !== null && (
                  <>
                    <JourneyList
                      journeys={journeys.data}
                      errorKey={journeys.errorKey}
                      onSelect={selectObject}
                      onOpenJourney={openJourney}
                    />
                    <ObjectSearch dataset={dataset} onSelect={selectObject} />
                    <DiagnosticList datasetId={dataset.id} onShow={showDiagnostic} />
                  </>
                )}
              </aside>
              <main className="content">
                {objectId === null ? (
                  <p className="hint">{t(dataset === null ? "app.empty" : "app.selectObject")}</p>
                ) : (
                  <>
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
                        selected={positionTarget === null ? selectedElement : null}
                        selectedTime={selection?.timeId ?? null}
                        onSelect={selectJourneyElement}
                        onSelectTime={selectTime}
                        onShowDiagnostic={showDiagnostic}
                      />
                    )}
                    {centerView === "object" && (
                      <ObjectView
                        objectId={objectId}
                        colors={appInfo.frameColors}
                        selectedElement={selectedElement}
                        onSelectElement={selectElement}
                        onNavigate={navigate}
                      />
                    )}
                  </>
                )}
              </main>
              <aside className="xml-column">
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
              </aside>
            </div>
          )}
        </div>
      </I18nContext.Provider>
    </DataSourceContext.Provider>
  );
}
