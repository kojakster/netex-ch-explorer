import { useEffect, useMemo, useState } from "react";
import { ApiError, type DataSource } from "./api";
import { FrameLegend } from "./components/FrameLegend";
import { GuideStatusBox } from "./components/GuideStatusBox";
import { HelpPage } from "./components/HelpPage";
import { IssueList } from "./components/IssueList";
import { LanguageSwitch } from "./components/LanguageSwitch";
import { DEFAULT_LANGUAGE, I18nContext, messagesFor, translate } from "./i18n";
import type { AppInfo, GuideInfo } from "./types";

type View = "main" | "help";

const LOAD_ERROR_KEY = "app.loadError";

interface AppProps {
  dataSource: DataSource;
}

export function App({ dataSource }: AppProps) {
  const [appInfo, setAppInfo] = useState<AppInfo | null>(null);
  const [guide, setGuide] = useState<GuideInfo | null>(null);
  const [errorKey, setErrorKey] = useState<string | null>(null);
  const [language, setLanguage] = useState(DEFAULT_LANGUAGE);
  const [view, setView] = useState<View>("main");

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
          setErrorKey(error instanceof ApiError ? error.key : LOAD_ERROR_KEY);
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

  return (
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
            </aside>
            <main className="content">
              <p>{t("app.empty")}</p>
            </main>
          </div>
        )}
      </div>
    </I18nContext.Provider>
  );
}
