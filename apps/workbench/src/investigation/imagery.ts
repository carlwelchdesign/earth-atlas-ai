import type { CaseAcquisition } from "./model";

export const NEPAL_IMAGERY_WINDOW = {
  start: "2026-07-27",
  end: "2026-09-24",
} as const;

export interface NepalImageryClient {
  listAcquisitions: (
    startDate: string,
    endDate: string,
    signal?: AbortSignal,
  ) => Promise<CaseAcquisition[]>;
}

function record(value: unknown, path: string): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new Error(`${path} must be an object.`);
  }
  return value as Record<string, unknown>;
}

function text(value: unknown, path: string) {
  if (typeof value !== "string" || !value) {
    throw new Error(`${path} must be text.`);
  }
  return value;
}

function number(value: unknown, path: string) {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    throw new Error(`${path} must be numeric.`);
  }
  return value;
}

function parseAcquisition(value: unknown, index: number): CaseAcquisition {
  const source = record(value, `acquisitions[${index}]`);
  const itemId = text(source.item_id, `acquisitions[${index}].item_id`);
  const imageUrl = text(source.image_url, `acquisitions[${index}].image_url`);
  const sourceUrl = text(
    source.source_url,
    `acquisitions[${index}].source_url`,
  );
  if (
    !/^\/api\/v1\/investigations\/nepal\/imagery\/[A-Za-z0-9_-]+\.png$/.test(
      imageUrl,
    )
  ) {
    throw new Error(`acquisitions[${index}].image_url is not approved.`);
  }
  if (new URL(sourceUrl).hostname !== "earth-search.aws.element84.com") {
    throw new Error(`acquisitions[${index}].source_url is not approved.`);
  }
  return {
    role: "before",
    itemId,
    productId: text(source.product_id, `acquisitions[${index}].product_id`),
    acquiredAt: text(source.acquired_at, `acquisitions[${index}].acquired_at`),
    imageUrl,
    thumbnail: imageUrl,
    sourceUrl,
    crs: text(source.crs, `acquisitions[${index}].crs`),
    resolutionMetres: number(
      source.resolution_metres,
      `acquisitions[${index}].resolution_metres`,
    ),
    cloudCoverPercent: number(
      source.cloud_cover_percent,
      `acquisitions[${index}].cloud_cover_percent`,
    ),
    cloudShadowPercent: number(
      source.cloud_shadow_percent,
      `acquisitions[${index}].cloud_shadow_percent`,
    ),
    nodataPercent: number(
      source.nodata_percent,
      `acquisitions[${index}].nodata_percent`,
    ),
  };
}

export class HttpNepalImageryClient implements NepalImageryClient {
  constructor(
    private readonly endpoint = "/api/v1/investigations/nepal/acquisitions",
  ) {}

  async listAcquisitions(
    startDate: string,
    endDate: string,
    signal?: AbortSignal,
  ): Promise<CaseAcquisition[]> {
    const query = new URLSearchParams({ start: startDate, end: endDate });
    const response = await fetch(`${this.endpoint}?${query}`, {
      signal,
      cache: "no-store",
    });
    if (!response.ok) {
      const body: unknown = await response.json().catch(() => null);
      const detail =
        typeof body === "object" && body !== null && "detail" in body
          ? String(body.detail)
          : `Imagery search failed (${response.status}).`;
      throw new Error(detail);
    }
    const body = record(await response.json(), "imagery response");
    if (body.maximum_range_days !== 60) {
      throw new Error("Imagery response did not preserve the 60-day boundary.");
    }
    if (!Array.isArray(body.acquisitions)) {
      throw new Error("Imagery response must include acquisitions.");
    }
    return body.acquisitions.map(parseAcquisition);
  }
}
