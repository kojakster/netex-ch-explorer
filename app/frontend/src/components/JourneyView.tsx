import { colorOf } from "../colors";
import { useI18n } from "../i18n";
import type {
  CategoryInfo,
  DiagnosticInfo,
  JourneyViewInfo,
  StopInfo,
  TimeInfo,
  TransportInfo,
} from "../types";
import { DiagnosticItems } from "./DiagnosticList";
import { Facilities } from "./Facilities";
import { FrameSwatch } from "./FrameLabel";
import { MasterText } from "./MasterText";
import { NoticeList } from "./NoticeList";
import { OperatingDays } from "./OperatingDays";
import { PartList } from "./PartList";
import { Sourced, ValueText } from "./Sourced";
import { StopTable } from "./StopTable";
import type { SourceProps } from "./sourceProps";

interface JourneyViewProps extends SourceProps {
  journey: JourneyViewInfo;
  selectedTime: string | null;
  onSelectTime: (time: TimeInfo, stop: StopInfo) => void;
  onShowDiagnostic: (diagnostic: DiagnosticInfo) => void;
}

function Transport({ transport, ...source }: SourceProps & { transport: TransportInfo }) {
  const { t } = useI18n();
  return (
    <div className="transport">
      <span className="badge">{t(`journey.role.${transport.role}`)}</span>{" "}
      {transport.mode.element !== null && (
        <>
          <Sourced element={transport.mode.element} {...source} className="flag">
            <span className="flag-name">{transport.mode.element.name}</span>=
            <code>{transport.mode.text}</code>
          </Sourced>{" "}
          <span className="master master-none">{t("master.none")}</span>
        </>
      )}
      {transport.submode.element !== null && (
        <>
          {" "}
          <Sourced element={transport.submode.element} {...source} className="flag">
            <span className="flag-name">{transport.submodeType}</span>=
            <code>{transport.submode.text}</code>
          </Sourced>{" "}
          <span className="master master-none">{t("master.none")}</span>
        </>
      )}
      {transport.mode.element === null && transport.submode.element === null && (
        <span className="lookup-missing">{t("lookup.absent")}</span>
      )}
    </div>
  );
}

function Category({
  category,
  guideCommit,
  ...source
}: SourceProps & { category: CategoryInfo; guideCommit: string | null }) {
  const { t } = useI18n();
  return (
    <div className="category">
      <span className="badge">{t(`journey.role.${category.role}`)}</span>{" "}
      {category.target === null ? (
        <Sourced element={category.ref} {...source}>
          {category.problem === null ? (
            t("lookup.absent")
          ) : (
            <ValueText value={category.problem} {...source} />
          )}
        </Sourced>
      ) : (
        <>
          <ValueText value={category.shortName} {...source} className="category-code" />{" "}
          {category.names.map((name) => (
            <span key={name.element.id} className="category-name">
              {name.lang !== null && <span className="lang">{name.lang}</span>} {name.text}{" "}
            </span>
          ))}
          <MasterText master={category.master} guideCommit={guideCommit} />
        </>
      )}
    </div>
  );
}

/** Die Fahrt als Fahrplan: Kopf, Betriebstage, Halte mit Zeiten, Angebote, Teilstrecken, Hinweise. */
export function JourneyView({
  journey,
  selectedTime,
  onSelectTime,
  onShowDiagnostic,
  ...source
}: JourneyViewProps) {
  const { t } = useI18n();
  const color = colorOf(journey.journey, source.colors);
  return (
    <article className="journey-view">
      <header>
        <h2>
          {color !== null && <FrameSwatch color={color} />}{" "}
          <Sourced element={journey.journey} {...source}>
            {journey.trainNumbers.length === 0
              ? journey.journey.name
              : journey.trainNumbers.map((number) => number.text ?? "").join(", ")}
          </Sourced>{" "}
          <code>{journey.journey.xmlId}</code>
        </h2>
        <dl className="journey-facts">
          <dt>{t("journey.trainNumber")}</dt>
          <dd>
            {journey.trainNumbers.length === 0 ? (
              <span className="lookup-missing">{t("lookup.absent")}</span>
            ) : (
              journey.trainNumbers.map((number) => (
                <span key={number.element?.id ?? number.text} className="list-item">
                  <ValueText value={number} {...source} />
                </span>
              ))
            )}
          </dd>
          {journey.privateCodes.length > 0 && (
            <>
              <dt>{t("journey.privateCode")}</dt>
              <dd>
                {journey.privateCodes.map((code) => (
                  <span key={code.element.id} className="list-item">
                    <Sourced element={code.element} {...source}>
                      {code.codeType !== null && (
                        <span className="flag-name">{code.codeType}=</span>
                      )}
                      <code>{code.value}</code>
                    </Sourced>
                  </span>
                ))}
              </dd>
            </>
          )}
          <dt>{t("journey.line")}</dt>
          <dd>
            <ValueText value={journey.line} {...source} />
          </dd>
          <dt>{t("journey.transport")}</dt>
          <dd>
            {journey.transports.map((transport) => (
              <Transport key={transport.owner.id} transport={transport} {...source} />
            ))}
          </dd>
          <dt>{t("journey.category")}</dt>
          <dd>
            {journey.categories.length === 0 ? (
              <span className="lookup-missing">{t("lookup.absent")}</span>
            ) : (
              journey.categories.map((category) => (
                <Category
                  key={category.ref.id}
                  category={category}
                  guideCommit={journey.guideCommit}
                  {...source}
                />
              ))
            )}
          </dd>
          <dt>{t("journey.pattern")}</dt>
          <dd>
            <ValueText value={journey.pattern} {...source} />
          </dd>
          <dt>{t("journey.timeDemand")}</dt>
          <dd>
            <ValueText value={journey.timeDemandType} {...source} />
          </dd>
          <dt>{t("journey.days")}</dt>
          <dd>
            <OperatingDays validities={journey.validities} {...source} />
          </dd>
        </dl>
      </header>

      <section aria-label={t("stops.title")}>
        <h3>{t("stops.title")}</h3>
        <StopTable
          journey={journey}
          selectedTime={selectedTime}
          onSelectTime={onSelectTime}
          {...source}
        />
        <p className="note">{t("stops.timesNote")}</p>
      </section>

      {journey.facilities.length > 0 && (
        <section aria-label={t("offers.title")}>
          <h3>{t("offers.title")}</h3>
          <Facilities sets={journey.facilities} guideCommit={journey.guideCommit} {...source} />
        </section>
      )}

      {journey.parts.length > 0 && (
        <section aria-label={t("parts.title")}>
          <h3>{t("parts.title")}</h3>
          <PartList journey={journey} {...source} />
        </section>
      )}

      {journey.notices.length > 0 && (
        <section aria-label={t("notices.title")}>
          <h3>{t("notices.title")}</h3>
          <NoticeList journey={journey} {...source} />
        </section>
      )}

      <section aria-label={t("journey.diagnostics")}>
        <h3>{t("journey.diagnostics")}</h3>
        {journey.diagnostics.length === 0 ? (
          <p className="note">{t("diagnostics.none")}</p>
        ) : (
          <DiagnosticItems diagnostics={journey.diagnostics} onShow={onShowDiagnostic} />
        )}
      </section>
    </article>
  );
}
