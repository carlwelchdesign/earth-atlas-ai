import type { CatalogSearchRequest, CatalogSearchResponse } from "./model";

export interface CatalogSearchClient {
  search: (
    request: CatalogSearchRequest,
    signal?: AbortSignal,
  ) => Promise<CatalogSearchResponse>;
}

export type CatalogFailureKind =
  "offline" | "permission" | "rate-limit" | "timeout" | "unknown";

export class CatalogClientError extends Error {
  constructor(
    message: string,
    readonly kind: CatalogFailureKind,
    options?: ErrorOptions,
  ) {
    super(message, options);
    this.name = "CatalogClientError";
  }
}

export class HttpCatalogSearchClient implements CatalogSearchClient {
  constructor(
    private readonly endpoint = "/v1/catalog/search",
    private readonly timeoutMs = 25_000,
  ) {}

  async search(
    request: CatalogSearchRequest,
    signal?: AbortSignal,
  ): Promise<CatalogSearchResponse> {
    const requestController = new AbortController();
    let timedOut = false;
    const timeoutId = window.setTimeout(() => {
      timedOut = true;
      requestController.abort();
    }, this.timeoutMs);
    const abortFromCaller = () => requestController.abort(signal?.reason);
    signal?.addEventListener("abort", abortFromCaller, { once: true });
    try {
      const response = await fetch(this.endpoint, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(request),
        signal: requestController.signal,
      });
      if (!response.ok) {
        const body: unknown = await response.json().catch(() => null);
        const detail =
          typeof body === "object" && body !== null && "detail" in body
            ? String(body.detail)
            : `Catalog search failed (${response.status}).`;
        const kind =
          response.status === 429
            ? "rate-limit"
            : response.status === 401 || response.status === 403
              ? "permission"
              : "unknown";
        throw new CatalogClientError(detail, kind);
      }
      return response.json() as Promise<CatalogSearchResponse>;
    } catch (error) {
      if (timedOut && !signal?.aborted) {
        throw new CatalogClientError(
          "The provider did not respond within the bounded 25-second window.",
          "timeout",
          { cause: error },
        );
      }
      if (error instanceof TypeError) {
        throw new CatalogClientError(
          "The catalog service could not be reached.",
          "offline",
          { cause: error },
        );
      }
      throw error;
    } finally {
      window.clearTimeout(timeoutId);
      signal?.removeEventListener("abort", abortFromCaller);
    }
  }
}

export interface PlaceSearchAdapter {
  resolve(
    query: string,
  ): Promise<{ label: string; bbox: [number, number, number, number] }>;
}

export class BoundedPlaceSearchAdapter implements PlaceSearchAdapter {
  resolve(query: string) {
    const normalized = query.trim().toLowerCase();
    if (normalized.includes("bingham canyon")) {
      return Promise.resolve({
        label: "Bingham Canyon, Utah",
        bbox: [-112.2, 40.45, -112.05, 40.6] as [
          number,
          number,
          number,
          number,
        ],
      });
    }
    const coordinates = query.split(",").map((part) => Number(part.trim()));
    if (coordinates.length === 2 && coordinates.every(Number.isFinite)) {
      const [latitude, longitude] = coordinates;
      const offset = 0.075;
      return Promise.resolve({
        label: `${latitude.toFixed(4)}, ${longitude.toFixed(4)}`,
        bbox: [
          longitude - offset,
          latitude - offset,
          longitude + offset,
          latitude + offset,
        ] as [number, number, number, number],
      });
    }
    return Promise.reject(
      new Error(
        "Place lookup is not configured yet. Enter latitude, longitude or Bingham Canyon, Utah.",
      ),
    );
  }
}
