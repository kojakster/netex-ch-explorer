import { act, renderHook, waitFor } from "@testing-library/react";
import { ApiError } from "./api";
import { LOAD_ERROR_KEY, useLoad } from "./data";

interface Deferred<T> {
  promise: Promise<T>;
  resolve: (value: T) => void;
  reject: (reason: unknown) => void;
}

function deferred<T>(): Deferred<T> {
  let resolve: (value: T) => void = () => undefined;
  let reject: (reason: unknown) => void = () => undefined;
  const promise = new Promise<T>((ok, fail) => {
    resolve = ok;
    reject = fail;
  });
  return { promise, resolve, reject };
}

describe("useLoad", () => {
  it("lädt Daten zum Schlüssel", async () => {
    const { result } = renderHook(() => useLoad("a", () => Promise.resolve("A")));
    await waitFor(() => expect(result.current.data).toBe("A"));
    expect(result.current.loading).toBe(false);
    expect(result.current.errorKey).toBeNull();
  });

  it("verwirft beim Schlüsselwechsel die alten Daten", async () => {
    const second = deferred<string>();
    const { result, rerender } = renderHook(
      ({ key }: { key: string }) =>
        useLoad(key, () => (key === "a" ? Promise.resolve("A") : second.promise)),
      { initialProps: { key: "a" } },
    );
    await waitFor(() => expect(result.current.data).toBe("A"));
    rerender({ key: "b" });
    await waitFor(() => expect(result.current.loading).toBe(true));
    expect(result.current.data).toBeNull();
    await act(async () => {
      second.resolve("B");
      await second.promise;
    });
    expect(result.current.data).toBe("B");
    expect(result.current.loading).toBe(false);
  });

  it("ignoriert die späte Antwort eines früheren Schlüssels", async () => {
    const first = deferred<string>();
    const { result, rerender } = renderHook(
      ({ key }: { key: string }) =>
        useLoad(key, () => (key === "a" ? first.promise : Promise.resolve("B"))),
      { initialProps: { key: "a" } },
    );
    rerender({ key: "b" });
    await waitFor(() => expect(result.current.data).toBe("B"));
    await act(async () => {
      first.resolve("A");
      await first.promise;
    });
    expect(result.current.data).toBe("B");
  });

  it("lädt bei null nichts und leert die Daten", async () => {
    const { result, rerender } = renderHook(
      ({ key }: { key: string | null }) => useLoad(key, () => Promise.resolve("A")),
      { initialProps: { key: "a" as string | null } },
    );
    await waitFor(() => expect(result.current.data).toBe("A"));
    rerender({ key: null });
    await waitFor(() => expect(result.current.data).toBeNull());
    expect(result.current.loading).toBe(false);
  });

  it("meldet den Fehlerschlüssel der API oder den allgemeinen", async () => {
    const api = renderHook(() =>
      useLoad("a", () => Promise.reject(new ApiError("error.not_found"))),
    );
    await waitFor(() => expect(api.result.current.errorKey).toBe("error.not_found"));
    const other = renderHook(() => useLoad("a", () => Promise.reject(new Error("x"))));
    await waitFor(() => expect(other.result.current.errorKey).toBe(LOAD_ERROR_KEY));
  });
});
