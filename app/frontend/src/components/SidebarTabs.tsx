import type { KeyboardEvent, ReactNode } from "react";
import { useI18n } from "../i18n";

export type SidebarTab = "journeys" | "objects" | "check";

interface SidebarTabsProps {
  active: SidebarTab;
  onChange: (tab: SidebarTab) => void;
  /** Anzahl der Befunde; `null`, solange noch nicht geprüft wurde. */
  findingCount: number | null;
  children: ReactNode;
}

const TABS: readonly SidebarTab[] = ["journeys", "objects", "check"];

/** Reiter, der auf eine Pfeil-, Pos1- oder Ende-Taste folgt; `null` bei jeder anderen Taste. */
export function tabAfterKey(active: SidebarTab, key: string): SidebarTab | null {
  const position = TABS.indexOf(active);
  switch (key) {
    case "ArrowRight":
      return TABS[(position + 1) % TABS.length] ?? null;
    case "ArrowLeft":
      return TABS[(position + TABS.length - 1) % TABS.length] ?? null;
    case "Home":
      return TABS[0] ?? null;
    case "End":
      return TABS[TABS.length - 1] ?? null;
    default:
      return null;
  }
}

/** Die drei Reiter der linken Spalte; der Inhalt des gewählten Reiters steht darunter. */
export function SidebarTabs({ active, onChange, findingCount, children }: SidebarTabsProps) {
  const { t } = useI18n();
  const label = (tab: SidebarTab): string =>
    tab === "check" && findingCount !== null
      ? t("tabs.checkCount", { count: findingCount })
      : t(`tabs.${tab}`);
  // Nur der gewählte Reiter ist mit Tab erreichbar; die Pfeiltasten wechseln und setzen den Fokus.
  const onKeyDown = (event: KeyboardEvent<HTMLButtonElement>) => {
    const next = tabAfterKey(active, event.key);
    if (next !== null) {
      event.preventDefault();
      onChange(next);
      document.getElementById(`sidebar-tab-${next}`)?.focus();
    }
  };
  return (
    <>
      <div className="tab-list" role="tablist" aria-label={t("tabs.title")}>
        {TABS.map((tab) => (
          <button
            key={tab}
            type="button"
            role="tab"
            id={`sidebar-tab-${tab}`}
            aria-selected={tab === active}
            aria-controls="sidebar-panel"
            className="tab"
            tabIndex={tab === active ? 0 : -1}
            onClick={() => onChange(tab)}
            onKeyDown={onKeyDown}
          >
            {label(tab)}
          </button>
        ))}
      </div>
      <div
        className="tab-panel"
        role="tabpanel"
        id="sidebar-panel"
        aria-labelledby={`sidebar-tab-${active}`}
      >
        {children}
      </div>
    </>
  );
}
