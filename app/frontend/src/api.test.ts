import { ApiError, HttpDataSource } from "./api";
import { APP_INFO } from "./testData";

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
});
