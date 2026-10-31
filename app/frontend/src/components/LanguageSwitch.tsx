import { useId } from "react";
import { useI18n } from "../i18n";

interface LanguageSwitchProps {
  languages: readonly string[];
  onChange: (language: string) => void;
}

/** Umschaltung der Oberflächensprache; Daten aus den Dateien werden nie übersetzt. */
export function LanguageSwitch({ languages, onChange }: LanguageSwitchProps) {
  const { language, t } = useI18n();
  const id = useId();
  return (
    <span className="language-switch">
      <label htmlFor={id}>{t("app.language")}</label>{" "}
      <select id={id} value={language} onChange={(event) => onChange(event.target.value)}>
        {languages.map((code) => (
          <option key={code} value={code}>
            {t(`language.${code}`)}
          </option>
        ))}
      </select>
    </span>
  );
}
