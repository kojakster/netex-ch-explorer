import { useI18n } from "../i18n";
import type { JourneyViewInfo, NoticeInfo } from "../types";
import { OperatingDays } from "./OperatingDays";
import { Sourced, ValueText } from "./Sourced";
import type { SourceProps } from "./sourceProps";

interface NoticeListProps extends SourceProps {
  journey: JourneyViewInfo;
}

function Range({ notice, journey }: { notice: NoticeInfo; journey: JourneyViewInfo }) {
  const { t } = useI18n();
  const nameAt = (position: number | null): string => {
    const stop = position === null ? undefined : journey.stops[position - 1];
    return stop?.stopPoint.text ?? "";
  };
  if (notice.startPosition !== null && notice.endPosition !== null) {
    return (
      <span className="note">
        {notice.startPosition === notice.endPosition
          ? t("notice.atStop", { stop: nameAt(notice.startPosition), number: notice.startPosition })
          : t("notice.range", {
              from: nameAt(notice.startPosition),
              fromNumber: notice.startPosition,
              to: nameAt(notice.endPosition),
              toNumber: notice.endPosition,
            })}
      </span>
    );
  }
  if (notice.startRef !== null || notice.endRef !== null) {
    return <span className="note">{t("notice.rangeNotPlaced")}</span>;
  }
  return null;
}

/** Hinweise (`NoticeAssignment` → `Notice`): Texte unverändert in allen Sprachen. */
export function NoticeList({ journey, ...source }: NoticeListProps) {
  const { t } = useI18n();
  return (
    <ul className="notice-list">
      {journey.notices.map((notice) => (
        <li key={notice.assignment.id} className="notice">
          <div>
            <Sourced element={notice.assignment} {...source} className="notice-id">
              {notice.notice?.xmlId ?? t("lookup.absent")}
            </Sourced>{" "}
            <ValueText value={notice.shortCode} {...source} />{" "}
            <span className="badge">{t(`notice.scope.${notice.scope}`)}</span>{" "}
            <Range notice={notice} journey={journey} />
          </div>
          {notice.problem !== null && (
            <div>
              <ValueText value={notice.problem} {...source} />
            </div>
          )}
          {notice.noticeType.status === "found" && (
            <div className="note">
              {t("notice.type")} <ValueText value={notice.noticeType} {...source} />
            </div>
          )}
          {notice.texts.map((entry) => (
            <div key={entry.text.element.id} className="notice-text">
              {entry.text.lang !== null && <span className="lang">{entry.text.lang}</span>}{" "}
              <Sourced element={entry.text.element} {...source}>
                {entry.text.text}
              </Sourced>
              {entry.alternativeFor !== null && (
                <span className="note">
                  {" "}
                  ({t("notice.alternative", { target: entry.alternativeFor })})
                </span>
              )}
            </div>
          ))}
          {notice.validity.length > 0 && (
            <div>
              <OperatingDays validities={notice.validity} {...source} />
            </div>
          )}
        </li>
      ))}
    </ul>
  );
}
