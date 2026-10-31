import { ApiError, HttpDataSource } from "./api";
import { APP_INFO, DATASET } from "./testData";

function fakeFetch(status: number, body: unknown): typeof fetch {
  return () =>
    Promise.resolve(
      new Response(typeof body === "string" ? body : JSON.stringify(body), { status }),
    );
}

describe("HttpDataSource", () => {
  it("liefert die Antwort als Objekt", async () => {
    const source = new HttpDataSource(fakeFetch(200, APP_INFO));
    await expect(source.getAppInfo()).resolves.toEqual(APP_INFO);
  });

  it("wirft ApiError mit dem Schlüssel aus dem Fehlerformat", async () => {
    const source = new HttpDataSource(
      fakeFetch(404, { error: { key: "error.not_found", params: {} } }),
    );
    await expect(source.getGuide()).rejects.toEqual(new ApiError("error.not_found"));
  });

  it("nutzt den allgemeinen Schlüssel bei Antwort ohne JSON", async () => {
    const source = new HttpDataSource(fakeFetch(500, "kaputt"));
    await expect(source.getGuide()).rejects.toMatchObject({ key: "error.http" });
  });

  it("nutzt den allgemeinen Schlüssel bei unerwartetem JSON", async () => {
    const source = new HttpDataSource(fakeFetch(500, { error: "x" }));
    await expect(source.getGuide()).rejects.toMatchObject({ key: "error.http" });
  });

  it("ruft die Herkunftskette über die Objekt-ID ab", async () => {
    const fetcher = vi.fn<typeof fetch>(() =>
      Promise.resolve(new Response(JSON.stringify([]), { status: 200 })),
    );
    await new HttpDataSource(fetcher).getProvenance("DS.1/2");
    expect(fetcher.mock.calls[0]?.[0]).toBe("api/objects/DS.1%2F2/provenance");
  });

  it("lädt Dateien als Multipart hoch, ohne eigenen Content-Type", async () => {
    const fetcher = vi.fn<typeof fetch>(() =>
      Promise.resolve(new Response(JSON.stringify(DATASET), { status: 200 })),
    );
    const file = new File(["<a/>"], "a.xml", { type: "text/xml" });
    await expect(new HttpDataSource(fetcher).openFiles([file, file])).resolves.toEqual(DATASET);
    const [path, init] = fetcher.mock.calls[0] ?? [];
    expect(path).toBe("api/datasets/upload");
    expect(init?.method).toBe("POST");
    const body = init?.body;
    expect(body).toBeInstanceOf(FormData);
    expect(body instanceof FormData ? body.getAll("files") : []).toHaveLength(2);
    expect(init?.headers).toEqual({ Accept: "application/json" });
  });

  it("startet die Validierung und schliesst Datensätze", async () => {
    const fetcher = vi.fn<typeof fetch>((input) =>
      Promise.resolve(
        String(input).includes("/validate")
          ? new Response(JSON.stringify(DATASET), { status: 200 })
          : new Response(null, { status: 204 }),
      ),
    );
    const source = new HttpDataSource(fetcher);
    await expect(source.validate("DS/1", false)).resolves.toEqual(DATASET);
    expect(fetcher.mock.calls[0]?.[0]).toBe("api/datasets/DS%2F1/validate");
    await source.validate("DS/1", true);
    expect(fetcher.mock.calls[1]?.[0]).toBe("api/datasets/DS%2F1/validate?forceCh20=true");
    expect(fetcher.mock.calls[0]?.[1]?.method).toBe("POST");
    await expect(source.closeDataset("DS/1")).resolves.toBeUndefined();
    expect(fetcher.mock.calls[2]?.[0]).toBe("api/datasets/DS%2F1");
    expect(fetcher.mock.calls[2]?.[1]?.method).toBe("DELETE");
  });

  it("meldet Fehler beim Schliessen mit dem Fehlerschlüssel", async () => {
    const source = new HttpDataSource(
      fakeFetch(404, { error: { key: "error.not_found", params: {} } }),
    );
    await expect(source.closeDataset("x")).rejects.toEqual(new ApiError("error.not_found"));
  });
});
