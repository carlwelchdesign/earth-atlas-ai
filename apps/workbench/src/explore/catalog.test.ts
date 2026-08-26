import { afterEach, describe, expect, it, vi } from "vitest";

import {
  CatalogClientError,
  HttpCatalogSearchClient,
  HttpPlaceSearchAdapter,
} from "./catalog";
import {
  BINGHAM_CANYON_BBOX,
  polygonFromBbox,
  type CatalogSearchRequest,
  type CatalogSearchResponse,
} from "./model";

const request: CatalogSearchRequest = {
  contract_version: "1.0.0",
  aoi: {
    bbox: BINGHAM_CANYON_BBOX,
    geometry: polygonFromBbox(BINGHAM_CANYON_BBOX),
  },
  start_at: "2025-06-01T00:00:00Z",
  end_at: "2025-08-01T00:00:00Z",
  providers: ["sentinel-1"],
  product_types: [],
  polarizations: [],
  max_resolution_m: null,
  page_size: 25,
  cursor: null,
};

const emptyResponse: CatalogSearchResponse = {
  contract_version: "1.0.0",
  query_id: "test",
  status: "empty",
  generated_at: "2025-08-25T00:00:00Z",
  cache: "miss",
  results: [],
  providers: [],
  warnings: [],
  next_cursor: null,
  sampled_result_count: 0,
};

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe("HttpCatalogSearchClient", () => {
  it("posts the versioned provider-neutral request", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(emptyResponse), {
        status: 200,
        headers: { "content-type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(
      new HttpCatalogSearchClient("/catalog").search(request),
    ).resolves.toEqual(emptyResponse);
    expect(fetchMock).toHaveBeenCalledWith(
      "/catalog",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify(request),
      }),
    );
  });

  it("surfaces a safe API detail", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: "AOI rejected" }), {
          status: 400,
          headers: { "content-type": "application/json" },
        }),
      ),
    );
    await expect(new HttpCatalogSearchClient().search(request)).rejects.toThrow(
      "AOI rejected",
    );
  });

  it.each([
    [401, "permission"],
    [403, "permission"],
    [429, "rate-limit"],
  ] as const)("classifies HTTP %s failures as %s", async (status, kind) => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: "Provider unavailable" }), {
          status,
          headers: { "content-type": "application/json" },
        }),
      ),
    );

    await expect(
      new HttpCatalogSearchClient().search(request),
    ).rejects.toMatchObject({ kind });
  });

  it("classifies a failed connection as offline", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed")));
    await expect(new HttpCatalogSearchClient().search(request)).rejects.toEqual(
      expect.objectContaining<Partial<CatalogClientError>>({
        kind: "offline",
        message: "The catalog service could not be reached.",
      }),
    );
  });

  it("bounds a provider request that never returns", async () => {
    vi.useFakeTimers();
    vi.stubGlobal(
      "fetch",
      vi.fn(
        (_url: string, init?: RequestInit) =>
          new Promise<Response>((_resolve, reject) => {
            init?.signal?.addEventListener("abort", () =>
              reject(new DOMException("Aborted", "AbortError")),
            );
          }),
      ),
    );
    const search = new HttpCatalogSearchClient("/catalog", 25).search(request);
    const rejection = expect(search).rejects.toThrow(
      "bounded 25-second window",
    );
    await vi.advanceTimersByTimeAsync(25);
    await rejection;
  });
});

describe("HttpPlaceSearchAdapter", () => {
  it("resolves coordinates locally without disclosing them to a provider", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    const result = await new HttpPlaceSearchAdapter().resolve(
      "38.5811, -121.4939",
    );
    expect(result).toMatchObject({
      label: "38.5811, -121.4939",
      provider: "Local coordinate resolver",
      attributionUrl: null,
    });
    expect(result.bbox).toEqual([
      expect.closeTo(-121.5689),
      expect.closeTo(38.5061),
      expect.closeTo(-121.4189),
      expect.closeTo(38.6561),
    ]);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("normalizes a bounded server-side place result", async () => {
    const fetchMock = vi
      .fn<(input: RequestInfo | URL, init?: RequestInit) => Promise<Response>>()
      .mockResolvedValue(
        new Response(
          JSON.stringify({
            label: "Sacramento, California, United States",
            bbox: [-121.568895, 38.5060606, -121.418895, 38.6560606],
            provider: "OpenStreetMap Nominatim",
            attribution_url: "https://www.openstreetmap.org/copyright",
          }),
          { status: 200, headers: { "content-type": "application/json" } },
        ),
      );
    vi.stubGlobal("fetch", fetchMock);

    await expect(
      new HttpPlaceSearchAdapter("/places").resolve("Sacramento"),
    ).resolves.toEqual({
      label: "Sacramento, California, United States",
      bbox: [-121.568895, 38.5060606, -121.418895, 38.6560606],
      provider: "OpenStreetMap Nominatim",
      attributionUrl: "https://www.openstreetmap.org/copyright",
    });
    expect(fetchMock).toHaveBeenCalledOnce();
    expect(fetchMock.mock.calls[0]?.[0]).toBe("/places");
    expect(fetchMock.mock.calls[0]?.[1]?.method).toBe("POST");
    expect(fetchMock.mock.calls[0]?.[1]?.body).toBe(
      JSON.stringify({ query: "Sacramento" }),
    );
    expect(fetchMock.mock.calls[0]?.[1]?.signal).toBeInstanceOf(AbortSignal);
  });

  it("rejects invalid untrusted place data", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            label: "Too broad",
            bbox: [-120, 30, -110, 40],
            provider: "Untrusted",
            attribution_url: null,
          }),
          { status: 200, headers: { "content-type": "application/json" } },
        ),
      ),
    );

    await expect(
      new HttpPlaceSearchAdapter().resolve("Too broad"),
    ).rejects.toThrow("25-square-degree limit");
  });
});
