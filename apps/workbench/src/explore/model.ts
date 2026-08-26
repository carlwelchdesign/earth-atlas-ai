export type ProviderId = "umbra" | "sentinel-1";
export type BBox = [number, number, number, number];

export interface PolygonGeometry {
  type: "Polygon";
  coordinates: number[][][];
}

export interface CatalogSearchRequest {
  contract_version: "1.0.0";
  aoi: { bbox: BBox; geometry: PolygonGeometry };
  start_at: string;
  end_at: string;
  providers: ProviderId[];
  product_types: string[];
  polarizations: string[];
  max_resolution_m: number | null;
  page_size: number;
  cursor: string | null;
}

export interface CatalogItem {
  provider: ProviderId;
  acquired_at: string;
  bbox: BBox;
  footprint: PolygonGeometry;
  product_type: string | null;
  polarizations: string[];
  resolution_range_m: number | null;
  resolution_azimuth_m: number | null;
  platform: string | null;
  observation_direction: string | null;
  orbit_state: string | null;
  incidence_angle_deg: number | null;
  license: { label: string; url: string | null };
  source: { item_id: string; collection: string; href: string };
}

export interface ProviderReport {
  provider: ProviderId;
  status: "complete" | "partial" | "failed";
  result_count: number;
  has_more: boolean;
  warning_count: number;
}

export interface CatalogWarning {
  code: string;
  message: string;
  provider: ProviderId | null;
  retryable: boolean;
}

export interface CatalogSearchResponse {
  contract_version: "1.0.0";
  query_id: string;
  status: "complete" | "empty" | "partial";
  generated_at: string;
  cache: "hit" | "miss";
  results: CatalogItem[];
  providers: ProviderReport[];
  warnings: CatalogWarning[];
  next_cursor: string | null;
  sampled_result_count: number;
}

export const BINGHAM_CANYON_BBOX: BBox = [-112.2, 40.45, -112.05, 40.6];

export function polygonFromBbox([
  west,
  south,
  east,
  north,
]: BBox): PolygonGeometry {
  return {
    type: "Polygon",
    coordinates: [
      [
        [west, south],
        [east, south],
        [east, north],
        [west, north],
        [west, south],
      ],
    ],
  };
}

export function validateBbox(values: number[]): BBox {
  if (values.length !== 4 || values.some((value) => !Number.isFinite(value))) {
    throw new Error(
      "Enter four valid WGS84 coordinates: west, south, east, north.",
    );
  }
  const [west, south, east, north] = values;
  if (
    west < -180 ||
    east > 180 ||
    south < -90 ||
    north > 90 ||
    west >= east ||
    south >= north
  ) {
    throw new Error(
      "The AOI coordinates must be ordered west, south, east, north.",
    );
  }
  if (
    east - west > 5 ||
    north - south > 5 ||
    (east - west) * (north - south) > 25
  ) {
    throw new Error("The AOI exceeds the supported 25-square-degree limit.");
  }
  return [west, south, east, north];
}

export function itemKey(item: CatalogItem): string {
  return `${item.provider}:${item.source.collection}:${item.source.item_id}`;
}

export function formatProvider(provider: ProviderId): string {
  return provider === "sentinel-1" ? "Sentinel-1" : "Umbra";
}
