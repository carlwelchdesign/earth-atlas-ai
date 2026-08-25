import { afterEach, describe, expect, it, vi } from "vitest";

import { demoBundle, loadWorkbenchBundle } from "./demo-bundle";

afterEach(() => {
  vi.unstubAllGlobals();
  window.history.replaceState({}, "", "/");
});

describe("loadWorkbenchBundle", () => {
  it("loads a prepared real bundle when it is available", async () => {
    const realBundle = {
      ...structuredClone(demoBundle),
      bundleId: "bundle-real",
      evidence: {
        ...structuredClone(demoBundle.evidence),
        lineage: "satellite-derived",
      },
    };
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(realBundle), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(loadWorkbenchBundle()).resolves.toEqual(realBundle);
    expect(fetchMock).toHaveBeenCalledWith("/generated-demo/bundle.json", {
      cache: "no-store",
    });
  });

  it("uses the explicit synthetic fallback when no prepared bundle exists", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(null, { status: 404 })),
    );

    await expect(loadWorkbenchBundle()).resolves.toMatchObject({
      bundleId: demoBundle.bundleId,
      evidence: { lineage: "synthetic-fixture" },
    });
  });

  it("does not hide malformed prepared JSON behind the synthetic fallback", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response("not-json", {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );

    await expect(loadWorkbenchBundle()).rejects.toThrow();
  });

  it("keeps named fixture scenarios deterministic", async () => {
    window.history.replaceState({}, "", "/?fixture=partial");
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    await expect(loadWorkbenchBundle()).resolves.toMatchObject({
      status: "partial",
      evidence: { lineage: "synthetic-fixture" },
    });
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
