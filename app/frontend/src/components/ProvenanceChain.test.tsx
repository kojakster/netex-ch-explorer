import { act, render, screen } from "@testing-library/react";
import { DataSourceContext } from "../data";
import { fakeSource, PROVENANCE } from "../testData";
import type { ChainLink } from "../types";
import { ProvenanceChain } from "./ProvenanceChain";

describe("ProvenanceChain", () => {
  it("zeigt beim Wechsel der Angabe nicht mehr die alte Kette", async () => {
    let finish: (chain: ChainLink[]) => void = () => undefined;
    const second = new Promise<ChainLink[]>((resolve) => {
      finish = resolve;
    });
    const source = fakeSource({
      getProvenance: (elementId) => (elementId === "e1" ? Promise.resolve(PROVENANCE) : second),
    });
    const view = (elementId: string) => (
      <DataSourceContext.Provider value={source}>
        <ProvenanceChain elementId={elementId} colors={[]} onSelect={() => undefined} />
      </DataSourceContext.Provider>
    );
    const { rerender } = render(view("e1"));
    expect(await screen.findAllByRole("button")).toHaveLength(PROVENANCE.length);
    rerender(view("e2"));
    expect(screen.queryAllByRole("button")).toHaveLength(0);
    await act(async () => {
      finish(PROVENANCE.slice(0, 1));
      await second;
    });
    expect(screen.getAllByRole("button")).toHaveLength(1);
  });
});
