import { useI18n } from "../i18n";
import type { CodeInfo, FacilitySetInfo } from "../types";
import { MasterText } from "./MasterText";
import { Sourced, ValueText } from "./Sourced";
import type { SourceProps } from "./sourceProps";

interface FacilitiesProps extends SourceProps {
  sets: readonly FacilitySetInfo[];
  guideCommit: string | null;
  compact?: boolean;
}

/** Schlüssel je Code; derselbe Code kann in einer Liste mehrfach stehen. */
function withKeys(codes: readonly CodeInfo[]): { key: string; code: CodeInfo }[] {
  const seen = new Map<string, number>();
  return codes.map((code) => {
    const count = (seen.get(code.code) ?? 0) + 1;
    seen.set(code.code, count);
    return { key: `${code.code}#${count}`, code };
  });
}

/** Angebote (`ServiceFacilitySet`): jeder Code unverändert, mit Bedeutung aus den Stammdaten. */
export function Facilities({ sets, guideCommit, compact = false, ...source }: FacilitiesProps) {
  const { t } = useI18n();
  return (
    <>
      {sets.map((set) => (
        <div key={set.ref.id} className="facility-set">
          {set.facilitySet === null ? (
            <Sourced element={set.ref} {...source}>
              {set.problem === null ? (
                t("lookup.absent")
              ) : (
                <ValueText value={set.problem} {...source} />
              )}
            </Sourced>
          ) : (
            !compact && (
              <Sourced element={set.facilitySet} {...source} className="facility-id">
                <code>{set.facilitySet.xmlId}</code>
              </Sourced>
            )
          )}
          {!compact &&
            set.description.map((text) => (
              <span key={text.element.id} className="facility-description">
                {text.lang !== null && <span className="lang">{text.lang}</span>} {text.text}
              </span>
            ))}
          <ul className="facility-groups">
            {set.groups.map((group) => (
              <li key={group.element.id}>
                {!compact && (
                  <Sourced element={group.element} {...source} className="facility-group">
                    {group.element.name}
                  </Sourced>
                )}
                {withKeys(group.codes).map(({ key, code }) => (
                  <span key={key} className="facility-code">
                    <Sourced element={code.element} {...source}>
                      <code>{code.code}</code>
                    </Sourced>{" "}
                    <MasterText master={code.master} guideCommit={guideCommit} compact={compact} />
                  </span>
                ))}
              </li>
            ))}
          </ul>
        </div>
      ))}
    </>
  );
}
