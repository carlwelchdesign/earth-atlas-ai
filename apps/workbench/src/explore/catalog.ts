import {
  validateBbox,
  type BBox,
  type CatalogSearchRequest,
  type CatalogSearchResponse,
} from "./model";

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
  resolve(query: string): Promise<PlaceSearchResult>;
}

export interface PlaceSearchResult {
  label: string;
  bbox: BBox;
  provider: string;
  attributionUrl: string | null;
}

export class HttpPlaceSearchAdapter implements PlaceSearchAdapter {
  constructor(
    private readonly endpoint = "/v1/places/resolve",
    private readonly timeoutMs = 10_000,
  ) {}

  async resolve(query: string): Promise<PlaceSearchResult> {
    const coordinateResult = resolveCoordinates(query);
    if (coordinateResult) return coordinateResult;
    const controller = new AbortController();
    const timeoutId = window.setTimeout(
      () => controller.abort(),
      this.timeoutMs,
    );
    try {
      const response = await fetch(this.endpoint, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ query: query.trim() }),
        signal: controller.signal,
      });
      if (!response.ok) {
        const body: unknown = await response.json().catch(() => null);
        const detail =
          typeof body === "object" && body !== null && "detail" in body
            ? String(body.detail)
            : "Place search did not complete.";
        throw new Error(detail);
      }
      const body: unknown = await response.json();
      if (typeof body !== "object" || body === null) {
        throw new Error("Place search returned invalid data.");
      }
      const label = "label" in body ? body.label : null;
      const bbox = "bbox" in body ? body.bbox : null;
      const provider = "provider" in body ? body.provider : null;
      const attributionUrl =
        "attribution_url" in body ? body.attribution_url : null;
      if (
        typeof label !== "string" ||
        !Array.isArray(bbox) ||
        !bbox.every((value) => typeof value === "number") ||
        typeof provider !== "string" ||
        (attributionUrl !== null && typeof attributionUrl !== "string")
      ) {
        throw new Error("Place search returned invalid data.");
      }
      return {
        label,
        bbox: validateBbox(bbox),
        provider,
        attributionUrl,
      };
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") {
        throw new Error("Place search timed out. Try again.", { cause: error });
      }
      throw error;
    } finally {
      window.clearTimeout(timeoutId);
    }
  }
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
        provider: "Local test resolver",
        attributionUrl: null,
      });
    }
    const coordinateResult = resolveCoordinates(query);
    if (coordinateResult) return Promise.resolve(coordinateResult);
    return Promise.reject(
      new Error(
        "Place lookup is not configured yet. Enter latitude, longitude or Bingham Canyon, Utah.",
      ),
    );
  }
}

function resolveCoordinates(query: string): PlaceSearchResult | null {
  const coordinates = query.split(",").map((part) => Number(part.trim()));
  if (coordinates.length !== 2 || !coordinates.every(Number.isFinite)) {
    return null;
  }
  const [latitude, longitude] = coordinates;
  if (latitude < -90 || latitude > 90 || longitude < -180 || longitude > 180) {
    throw new Error("Latitude must be -90 to 90 and longitude -180 to 180.");
  }
  const offset = 0.075;
  const rounded = (value: number) => Number(value.toFixed(6));
  return {
    label: `${latitude.toFixed(4)}, ${longitude.toFixed(4)}`,
    bbox: validateBbox([
      rounded(Math.max(-180, longitude - offset)),
      rounded(Math.max(-90, latitude - offset)),
      rounded(Math.min(180, longitude + offset)),
      rounded(Math.min(90, latitude + offset)),
    ]),
    provider: "Local coordinate resolver",
    attributionUrl: null,
  };
}
