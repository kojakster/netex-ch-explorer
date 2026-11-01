import { fireEvent, render, screen, within } from "@testing-library/react";
import { I18nContext, messagesFor, translate } from "../i18n";
import { OriginContext } from "../origin";
import { JOURNEY_VIEW } from "../testData";
import type {
  CategoryInfo,
  DiagnosticInfo,
  JourneyViewInfo,
  MasterInfo,
  NoticeInfo,
  TimeInfo,
  TransportInfo,
  ValidityInfo,
} from "../types";
import { CalculationChain } from "./CalculationChain";
import { Facilities } from "./Facilities";
import { JourneyView } from "./JourneyView";
import { MasterText } from "./MasterText";
import { NoticeList } from "./NoticeList";
import { OperatingDays } from "./OperatingDays";
import { StopTable } from "./StopTable";
import { TimeCell } from "./TimeCell";

const COLORS = [{ key: "ServiceFrame", background: "#1B8A2F", text: "#000000" }];

function withLanguage(language: string, children: React.ReactNode) {
  const messages = messagesFor(language);
  return (
    <I18nContext.Provider
      value={{ language, t: (key, params) => translate(messages, key, params) }}
    >
      {children}
    </I18nContext.Provider>
  );
}

const PROPS = { colors: COLORS, selected: null, onSelect: () => undefined };

describe("MasterText", () => {
  const found: MasterInfo = {
    status: "found",
    matches: [
      {
        sheet: "Angebote",
        row: 90,
        texts: [
          { label: "Angebotabkürzung", text: "VB" },
          { label: "Angebottext", text: "Velos" },
          { label: "Facility", text: "LuggageCarriageType" },
        ],
      },
      { sheet: "Angebote", row: 91, texts: [{ label: "Angebotabkürzung", text: "VC" }] },
    ],
  };

  it("zeigt Blatt, Zeile und Guide-Stand zu jeder Zeile", () => {
    render(<MasterText master={found} guideCommit="b7ac15860369" />);
    expect(screen.getByText(/Blatt „Angebote“, Zeile 90, Guide b7ac158/)).toBeTruthy();
    expect(screen.getByText(/Blatt „Angebote“, Zeile 91/)).toBeTruthy();
    expect(screen.getByText("Velos")).toBeTruthy();
  });

  it("kürzt in der Tabellenzelle auf zwei Werte je Zeile", () => {
    render(<MasterText master={found} guideCommit={null} compact />);
    expect(screen.getByText("VB · Velos")).toBeTruthy();
    expect(screen.queryByText("LuggageCarriageType")).toBeNull();
  });

  it("sagt, wenn es keine Erläuterung gibt oder die Tabelle fehlt", () => {
    const { rerender } = render(
      <MasterText master={{ status: "none", matches: [] }} guideCommit={null} />,
    );
    expect(screen.getByText("keine Erläuterung in den Stammdaten")).toBeTruthy();
    rerender(<MasterText master={{ status: "unavailable", matches: [] }} guideCommit={null} />);
    expect(screen.getByText("Mappingtabelle nicht verfügbar")).toBeTruthy();
    rerender(<MasterText master={null} guideCommit={null} />);
    expect(screen.queryByText(/Stammdaten|Mappingtabelle/)).toBeNull();
  });
});

describe("TimeCell", () => {
  const base: TimeInfo = {
    id: "arrival-2",
    status: "computed",
    clock: "00:17:00",
    dayOffset: 1,
    offsetOrigin: "computed",
    source: null,
    chain: [],
    reason: null,
  };

  it("zeigt Tageswechsel und Markierung „berechnet“", () => {
    render(<TimeCell time={base} selectedTime={null} onSelect={() => undefined} />);
    expect(screen.getByText("00:17")).toBeTruthy();
    const marker = screen.getByText("+1");
    expect(marker.getAttribute("title")).toContain("Tageswechsel berechnet");
    // Berechnete Zeiten tragen ein Symbol mit Beschriftung, keine Textzeile.
    const symbol = screen.getByRole("img", { name: "berechnet" });
    expect(symbol.textContent).toBe("Σ");
    expect(screen.queryByText("berechnet")).toBeNull();
  });

  it("setzt die Abfahrt fett und die Ankunft normal", () => {
    const { rerender } = render(
      <TimeCell time={base} selectedTime={null} onSelect={() => undefined} />,
    );
    expect(screen.getByRole("button").className).not.toContain("time-strong");
    rerender(<TimeCell time={base} selectedTime={null} onSelect={() => undefined} strong />);
    expect(screen.getByRole("button").className).toContain("time-strong");
  });

  it("zeigt „−1“ und lässt bei ausdrücklicher Zeit die Markierung weg", () => {
    const explicit: TimeInfo = { ...base, status: "explicit", dayOffset: -1, offsetOrigin: null };
    render(<TimeCell time={explicit} selectedTime="arrival-2" onSelect={() => undefined} />);
    expect(screen.getByText("−1").getAttribute("title")).toBeNull();
    expect(screen.queryByRole("img", { name: "berechnet" })).toBeNull();
    expect(screen.getByRole("button").className).toContain("selected");
  });

  it("zeigt ohne Zeit einen Strich und meldet die Wahl der Zeit", () => {
    const onSelect = vi.fn();
    const { rerender } = render(<TimeCell time={null} selectedTime={null} onSelect={onSelect} />);
    expect(screen.queryByRole("button")).toBeNull();
    rerender(<TimeCell time={base} selectedTime={null} onSelect={onSelect} />);
    fireEvent.click(screen.getByRole("button"));
    expect(onSelect).toHaveBeenCalledWith(base);
  });

  it("zeigt „nicht berechenbar“ auch ohne Grund", () => {
    const failed: TimeInfo = { ...base, status: "not_computable", clock: null, reason: null };
    render(<TimeCell time={failed} selectedTime={null} onSelect={() => undefined} />);
    expect(screen.getByText("nicht berechenbar")).toBeTruthy();
  });
});

describe("OperatingDays", () => {
  const days = JOURNEY_VIEW.validities[0]?.days;
  if (days === null || days === undefined) {
    throw new Error("Testdaten ohne Betriebstage");
  }

  it("klappt die Tage auf und zeigt keine Wochentage", () => {
    render(<OperatingDays validities={JOURNEY_VIEW.validities} {...PROPS} />);
    expect(screen.getByText("14.12.2026")).toBeTruthy();
    expect(screen.queryByText(/Mo|Fr/)).toBeNull();
  });

  it("zeigt Daten im ISO-Format in englischer Oberfläche", () => {
    render(withLanguage("en", <OperatingDays validities={JOURNEY_VIEW.validities} {...PROPS} />));
    expect(screen.getByText("2026-12-14")).toBeTruthy();
    expect(screen.getByText(/2026-12-13 to 2026-12-19: 7 days in the period/)).toBeTruthy();
  });

  it("listet die Tage nicht auf, wenn sie sich nicht sicher bestimmen lassen", () => {
    const unlisted: ValidityInfo[] = [
      {
        ...(JOURNEY_VIEW.validities[0] as ValidityInfo),
        days: {
          ...days,
          daysListed: false,
          days: [],
          firstDay: null,
          lastDay: null,
          validCount: 1,
        },
      },
    ];
    render(<OperatingDays validities={unlisted} {...PROPS} />);
    expect(screen.getByText(/Die Tage werden nicht aufgelistet/)).toBeTruthy();
    expect(screen.queryByText("14.12.2026")).toBeNull();
  });

  it("zeigt ohne Bedingung oder bei nicht aufgelöster Bedingung den Grund", () => {
    const { rerender } = render(<OperatingDays validities={[]} {...PROPS} />);
    expect(screen.getByText(/Keine Betriebstage in der Datei/)).toBeTruthy();
    const ref = (JOURNEY_VIEW.validities[0] as ValidityInfo).ref;
    rerender(<OperatingDays validities={[{ ref, days: null, problem: null }]} {...PROPS} />);
    expect(screen.getByText("AvailabilityCondition nicht aufgelöst")).toBeTruthy();
    rerender(
      <OperatingDays
        validities={[
          { ref, days: null, problem: { status: "not_resolved", text: "ac-x", element: ref } },
        ]}
        {...PROPS}
      />,
    );
    expect(screen.getByText("ac-x: nicht in dieser Datei aufgelöst")).toBeTruthy();
  });
});

describe("Facilities", () => {
  it("zeigt gleiche Codes in einer Liste getrennt und die Gruppe beim Namen", () => {
    const set = JOURNEY_VIEW.parts[0]?.facilities[0];
    if (set === undefined) {
      throw new Error("Testdaten ohne Angebote");
    }
    const code = set.groups[0]?.codes[0];
    if (code === undefined) {
      throw new Error("Testdaten ohne Code");
    }
    const doubled = {
      ...set,
      groups: [{ ...(set.groups[0] as (typeof set.groups)[0]), codes: [code, code] }],
    };
    render(<Facilities sets={[doubled]} guideCommit={null} {...PROPS} />);
    expect(screen.getAllByText("bistro")).toHaveLength(2);
    expect(screen.getByText("CateringFacilityList")).toBeTruthy();
  });

  it("zeigt den Grund, wenn das Angebot nicht aufgelöst ist", () => {
    const set = JOURNEY_VIEW.parts[0]?.facilities[0];
    if (set === undefined) {
      throw new Error("Testdaten ohne Angebote");
    }
    const broken = {
      ...set,
      facilitySet: null,
      groups: [],
      problem: { status: "not_resolved" as const, text: "fs-x", element: set.ref },
    };
    render(<Facilities sets={[broken]} guideCommit={null} {...PROPS} />);
    expect(screen.getByText("fs-x: nicht in dieser Datei aufgelöst")).toBeTruthy();
  });
});

describe("StopTable", () => {
  function table(journey: JourneyViewInfo) {
    return (
      <StopTable journey={journey} selectedTime={null} onSelectTime={() => undefined} {...PROPS} />
    );
  }

  it("meldet ohne Haltefolge den Grund", () => {
    render(table({ ...JOURNEY_VIEW, stops: [] }));
    expect(screen.getByText(/Keine Haltefolge verfügbar/)).toBeTruthy();
  });

  it("sagt „Haltestelle nicht in dieser Datei“, wenn weder Haltestelle noch Kante vorliegen", () => {
    const external = {
      status: "external_or_unloaded" as const,
      text: "ch:1:sloid:1",
      element: null,
    };
    const stops = JOURNEY_VIEW.stops.map((stop) => ({
      ...stop,
      stopPlace: external,
      quay: external,
    }));
    render(table({ ...JOURNEY_VIEW, stops }));
    expect(screen.getAllByText(/Haltestelle nicht in dieser Datei/)).toHaveLength(3);
  });

  it("sagt Ein-/Aussteigen nur in Worten, wenn es eingeschränkt ist, und zeigt Bedarfshalt und StopUse", () => {
    const first = JOURNEY_VIEW.stops[0];
    const second = JOURNEY_VIEW.stops[1];
    if (first === undefined || second === undefined) {
      throw new Error("Testdaten ohne Halte");
    }
    const flag = (text: string) => ({ ...first.forBoarding, text });
    const stops = [
      { ...first, forBoarding: flag("false"), forAlighting: flag("false") },
      {
        ...second,
        forBoarding: flag("true"),
        forAlighting: flag("true"),
        requestStop: flag("true"),
        stopUse: {
          code: "access",
          element: first.point,
          master: {
            status: "found" as const,
            matches: [{ sheet: "StopUse", row: 4, texts: [{ label: "Usage", text: "Default" }] }],
          },
        },
      },
      { ...second, forBoarding: flag("?"), forAlighting: flag("true") },
    ];
    render(
      <OriginContext.Provider value={false}>
        {table({ ...JOURNEY_VIEW, stops })}
      </OriginContext.Provider>,
    );
    const rows = screen.getAllByRole("row");
    expect(within(rows[1] as HTMLElement).getByText("kein Ein-/Aussteigen")).toBeTruthy();
    // Uneingeschränktes Ein- und Aussteigen und die Werte ForBoarding/ForAlighting bleiben weg.
    expect(within(rows[2] as HTMLElement).queryByText("Ein- und Aussteigen")).toBeNull();
    expect(screen.queryByText("ForBoarding")).toBeNull();
    expect(within(rows[2] as HTMLElement).getByText("Bedarfshalt")).toBeTruthy();
    expect(within(rows[2] as HTMLElement).getByText("Default")).toBeTruthy();
    expect(
      within(rows[3] as HTMLElement).getByText(/nicht \(vollständig\) angegeben/),
    ).toBeTruthy();
  });
});

describe("NoticeList", () => {
  const notice = JOURNEY_VIEW.notices[0];
  if (notice === undefined) {
    throw new Error("Testdaten ohne Hinweis");
  }

  function list(overrides: Partial<NoticeInfo>) {
    return (
      <NoticeList
        journey={{ ...JOURNEY_VIEW, notices: [Object.assign({}, notice, overrides)] }}
        {...PROPS}
      />
    );
  }

  it("zeigt die Strecke eines Hinweises mit Halten dieser Fahrt", () => {
    const { rerender } = render(list({ startPosition: 1, endPosition: 3 }));
    expect(
      screen.getByText(/ab Halt 1 \(Synthetisch A\) bis Halt 3 \(Synthetisch C\)/),
    ).toBeTruthy();
    rerender(list({ startPosition: 2, endPosition: 2 }));
    expect(screen.getByText("am Halt 2 (Synthetisch B)")).toBeTruthy();
    rerender(list({ startRef: notice.assignment }));
    expect(screen.getByText(/nennt Halte, die nicht zu dieser Fahrt gehören/)).toBeTruthy();
  });

  it("kennzeichnet AlternativeText und zeigt nicht aufgelöste Hinweise", () => {
    const text = notice.texts[0];
    if (text === undefined) {
      throw new Error("Testdaten ohne Text");
    }
    const { rerender } = render(
      list({ texts: [{ ...text, alternativeFor: "Text" }], noticeType: notice.shortCode }),
    );
    expect(screen.getByText(/AlternativeText für Text/)).toBeTruthy();
    expect(screen.getByText(/Art des Hinweises:/)).toBeTruthy();
    rerender(
      list({
        notice: null,
        texts: [],
        problem: { status: "not_resolved", text: "n-x", element: notice.ref },
      }),
    );
    expect(screen.getByText("n-x: nicht in dieser Datei aufgelöst")).toBeTruthy();
  });
});

describe("CalculationChain", () => {
  it("zeigt nichts für eine unbekannte Zeit", () => {
    const { container } = render(
      <CalculationChain journey={JOURNEY_VIEW} timeId="arrival-9" {...PROPS} />,
    );
    expect(container.textContent).toBe("");
  });

  it("zeigt Abfahrt am ersten Halt mit Quelle und ohne Berechnungsvermerk", () => {
    render(<CalculationChain journey={JOURNEY_VIEW} timeId="departure-1" {...PROPS} />);
    expect(screen.getByText(/Abfahrt an Halt 1 \(Synthetisch A\):/)).toBeTruthy();
    expect(screen.getByText("steht so in der Datei")).toBeTruthy();
  });

  it("zeigt den Grund und seine Stelle bei einer nicht berechenbaren Zeit", () => {
    const onSelect = vi.fn();
    render(
      <CalculationChain
        journey={JOURNEY_VIEW}
        timeId="arrival-3"
        colors={COLORS}
        selected={null}
        onSelect={onSelect}
      />,
    );
    fireEvent.click(screen.getByText(/Im TimeDemandType fehlt für den TimingLink tl-2/));
    expect(onSelect).toHaveBeenCalledWith("SYNTHETICDATASET01.121");
  });
});

describe("keine verschachtelten Knöpfe", () => {
  const ref = (JOURNEY_VIEW.validities[0] as ValidityInfo).ref;
  const problem = { status: "not_resolved" as const, text: "x", element: ref };

  it("ein Grund erzeugt genau einen Knopf und ein Klick genau eine Auswahl", () => {
    const onSelect = vi.fn();
    const { container } = render(
      <OperatingDays validities={[{ ref, days: null, problem }]} {...PROPS} onSelect={onSelect} />,
    );
    expect(container.querySelector("button button")).toBeNull();
    expect(container.querySelectorAll("button")).toHaveLength(1);
    fireEvent.click(screen.getByRole("button"));
    expect(onSelect).toHaveBeenCalledTimes(1);
    expect(onSelect).toHaveBeenCalledWith(ref.id);
  });

  it("die Fahrtansicht mit nicht aufgelösten Angeboten und Kategorien hat keinen Knopf im Knopf", () => {
    const set = JOURNEY_VIEW.parts[0]?.facilities[0];
    if (set === undefined) {
      throw new Error("Testdaten ohne Angebote");
    }
    const category: CategoryInfo = {
      role: "journey",
      ref,
      target: null,
      problem,
      shortName: problem,
      names: [],
      master: null,
    };
    const broken: JourneyViewInfo = {
      ...JOURNEY_VIEW,
      validities: [{ ref, days: null, problem }],
      facilities: [{ ...set, facilitySet: null, groups: [], problem }],
      categories: [category],
    };
    const { container } = render(
      <JourneyView
        journey={broken}
        selectedTime={null}
        onSelectTime={() => undefined}
        onShowDiagnostic={() => undefined}
        showOrigin
        onShowOriginChange={() => undefined}
        {...PROPS}
      />,
    );
    expect(container.querySelector("button button")).toBeNull();
  });
});

describe("StopTable ohne und mit „Herkunft zeigen“", () => {
  function table(showOrigin: boolean, journey: JourneyViewInfo = JOURNEY_VIEW) {
    return (
      <OriginContext.Provider value={showOrigin}>
        <StopTable
          journey={journey}
          selectedTime={null}
          onSelectTime={() => undefined}
          {...PROPS}
        />
      </OriginContext.Provider>
    );
  }

  it("zeigt in der Normalansicht keine Zusatzzeilen und keine Farbbalken", () => {
    render(table(false));
    expect(screen.queryByText("Haltestelle (StopPlace)")).toBeNull();
    expect(screen.queryByText("ForBoarding")).toBeNull();
    const names = document.querySelectorAll(".stop-name");
    expect(names.length).toBe(3);
    for (const name of names) {
      expect(name.className).toContain("sourced-plain");
      expect((name as HTMLElement).style.borderLeftColor).toBe("");
    }
  });

  it("zeigt mit „Herkunft zeigen“ StopPlace, Quay und die Werte von ForBoarding/ForAlighting", () => {
    render(table(true));
    expect(screen.getAllByText("Haltestelle (StopPlace)")).toHaveLength(3);
    expect(screen.getAllByText("Kante (Quay)")).toHaveLength(3);
    expect(screen.getAllByText("ForBoarding").length).toBeGreaterThan(0);
    expect((document.querySelector(".stop-name") as HTMLElement).style.borderLeftColor).not.toBe(
      "",
    );
  });

  it("nennt die Spalte „Gleis“ bei rail der Fahrt und sonst „Kante“", () => {
    const { rerender } = render(table(false));
    expect(screen.getByRole("columnheader", { name: "Gleis" })).toBeTruthy();
    const bus = {
      ...JOURNEY_VIEW,
      transports: JOURNEY_VIEW.transports.map((transport) => ({
        ...transport,
        mode: { ...transport.mode, text: "bus" },
      })),
    };
    rerender(table(false, bus));
    expect(screen.getByRole("columnheader", { name: "Kante" })).toBeTruthy();
    // Fehlt der TransportMode der Fahrt, gilt der der Linie.
    const lineRail: JourneyViewInfo = {
      ...JOURNEY_VIEW,
      transports: [
        {
          ...(JOURNEY_VIEW.transports[0] as TransportInfo),
          mode: { status: "absent", text: null, element: null },
        },
        {
          ...(JOURNEY_VIEW.transports[0] as TransportInfo),
          role: "line",
        },
      ],
    };
    rerender(table(false, lineRail));
    expect(screen.getByRole("columnheader", { name: "Gleis" })).toBeTruthy();
    rerender(table(false, { ...JOURNEY_VIEW, transports: [] }));
    expect(screen.getByRole("columnheader", { name: "Kante" })).toBeTruthy();
  });

  it("beginnt die Haltelinie am ersten und endet sie am letzten Halt", () => {
    render(table(false));
    const rows = document.querySelectorAll(".stop-row");
    expect(rows[0]?.className).toContain("stop-first");
    expect(rows[2]?.className).toContain("stop-last");
    expect(rows[1]?.className).not.toMatch(/stop-first|stop-last/);
    expect(document.querySelectorAll(".line-cell").length).toBe(3);
  });
});

describe("JourneyView als Fahrplananzeige", () => {
  function view(overrides: Partial<JourneyViewInfo> = {}, showOrigin = false) {
    const onShowOriginChange = vi.fn();
    const onSelect = vi.fn();
    render(
      <JourneyView
        journey={{ ...JOURNEY_VIEW, ...overrides }}
        selectedTime={null}
        onSelectTime={() => undefined}
        onShowDiagnostic={() => undefined}
        showOrigin={showOrigin}
        onShowOriginChange={onShowOriginChange}
        colors={COLORS}
        selected={null}
        onSelect={onSelect}
      />,
    );
    return { onShowOriginChange, onSelect };
  }

  it("zeigt im Kopf Zugnummer, Von → Nach, Betreiber, Gültigkeit und Betriebstage", () => {
    view();
    const head = document.querySelector(".journey-head") as HTMLElement;
    expect(within(head).getByRole("heading").textContent).toContain("1");
    expect(within(head).getByText("Synthetisch A")).toBeTruthy();
    expect(within(head).getByText("Synthetisch C")).toBeTruthy();
    expect(within(head).getByText("Synthetische Bahn")).toBeTruthy();
    expect(within(head).getByText("Gültig 13.12.2026 bis 19.12.2026")).toBeTruthy();
    expect(within(head).getByText("5 Betriebstage (7 Tage im Zeitraum)")).toBeTruthy();
  });

  it("schreibt bei einem Betriebstag und einem Tag im Zeitraum die Einzahl", () => {
    const [validity] = JOURNEY_VIEW.validities;
    if (validity === undefined || validity.days === null) {
      throw new Error("Testdaten ohne Betriebstage");
    }
    view({
      validities: [{ ...validity, days: { ...validity.days, validCount: 1, periodDays: 1 } }],
    });
    const head = document.querySelector(".journey-head") as HTMLElement;
    expect(within(head).getByText("1 Betriebstag (1 Tag im Zeitraum)")).toBeTruthy();
  });

  it("zeigt die Legende der Frame-Farben nur einmal, auch bei offener Aufbau-Übersicht", () => {
    view({}, true);
    (document.querySelector(".structure") as HTMLDetailsElement).open = true;
    expect(document.querySelectorAll(".legend").length).toBe(1);
  });

  it("zeigt die Legende ohne „Herkunft zeigen“ nur in der Aufbau-Übersicht", () => {
    view({}, false);
    expect(document.querySelectorAll(".legend").length).toBe(1);
    expect(document.querySelector(".structure .legend")).not.toBeNull();
  });

  it("zeigt das Abzeichen der Produktkategorie in der Überschrift, wenn sie vorliegt", () => {
    const category: CategoryInfo = {
      role: "journey",
      ref: (JOURNEY_VIEW.validities[0] as ValidityInfo).ref,
      target: (JOURNEY_VIEW.validities[0] as ValidityInfo).ref,
      problem: null,
      shortName: { status: "found", text: "RE", element: JOURNEY_VIEW.journey },
      names: [],
      master: null,
    };
    view({ categories: [category] });
    expect(
      within(document.querySelector(".journey-head") as HTMLElement).getByText("RE").className,
    ).toContain("badge");
  });

  it("kennzeichnet fehlende Angaben im Kopf, statt etwas zu ergänzen", () => {
    view({
      trainNumbers: [],
      validities: [],
      operator: { status: "absent", text: null, element: null },
      stops: [],
    });
    const head = document.querySelector(".journey-head") as HTMLElement;
    expect(within(head).getAllByText("nicht in der Datei").length).toBe(2);
    expect(within(head).getByText(/Keine Betriebstage in der Datei/)).toBeTruthy();
    expect(head.querySelector(".journey-route")).toBeNull();
  });

  it("zeigt Warnungen und Hinweise der Fahrt als Abzeichen, die zu den Befunden springen", () => {
    const scroll = vi.fn();
    Element.prototype.scrollIntoView = scroll;
    const diagnostics = [
      { ...(JOURNEY_VIEW.diagnostics[0] as DiagnosticInfo), severity: "warning" as const },
      { ...(JOURNEY_VIEW.diagnostics[0] as DiagnosticInfo), severity: "warning" as const },
      { ...(JOURNEY_VIEW.diagnostics[0] as DiagnosticInfo), severity: "info" as const },
    ];
    view({ diagnostics });
    expect(screen.getByRole("button", { name: /Warnung 2/ })).toBeTruthy();
    expect(screen.queryByRole("button", { name: /Fehler/ })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: /Hinweis 1/ }));
    expect(scroll).toHaveBeenCalled();
  });

  it("schaltet „Herkunft zeigen“ und zeigt dann die Legende der Frame-Farben", () => {
    const { onShowOriginChange } = view();
    expect(document.querySelector(".origin-bar + .legend")).toBeNull();
    fireEvent.click(screen.getByRole("checkbox", { name: "Herkunft zeigen" }));
    expect(onShowOriginChange).toHaveBeenCalledWith(true);
  });

  it("zeigt mit eingeschalteter Herkunft die Legende und die Farbbalken", () => {
    view({}, true);
    expect(document.querySelector(".origin-bar + .legend")).not.toBeNull();
    expect((screen.getByRole("checkbox") as HTMLInputElement).checked).toBe(true);
  });

  it("klappt alle übrigen Angaben unter „Weitere Angaben“ ein, mit Bezeichnung und NeTEx-Name", () => {
    view();
    const more = screen.getByText("Weitere Angaben").closest("details") as HTMLDetailsElement;
    expect(more.open).toBe(false);
    expect(within(more).getByText(/Fahrtmuster/)).toBeTruthy();
    expect(within(more).getByText("· ServiceJourneyPattern")).toBeTruthy();
    expect(within(more).getByText("· TimeDemandType")).toBeTruthy();
    expect(within(more).getByText("Teilstrecken")).toBeTruthy();
    expect(within(more).getByText("Synthetischer Hinweis")).toBeTruthy();
  });
});
