import type { ReactNode } from "react";
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

/** Die drei Reiter der linken Spalte; der Inhalt des gewählten Reiters steht darunter. */
export function SidebarTabs({ active, onChange, findingCount, children }: SidebarTabsProps) {
  const { t } = useI18n();
  const label = (tab: SidebarTab): string =>
    tab === "check" && findingCount !== null
      ? t("tabs.checkCount", { count: findingCount })
      : t(`tabs.${tab}`);
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
            onClick={() => onChange(tab)}
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
