import type { BBox, CatalogItem, PolygonGeometry } from "./model";

export type AnalysisJobStatus =
  "queued" | "running" | "succeeded" | "failed" | "cancelled";

export interface ComparabilityEvidence {
  temporal_separation_seconds: number;
  common_footprint: PolygonGeometry;
  common_bbox: BBox;
  before_overlap_percent: number;
  after_overlap_percent: number;
  same_product: boolean;
  shared_polarizations: string[];
  range_resolution_delta_percent: number;
  azimuth_resolution_delta_percent: number;
  same_observation_direction: boolean;
  same_orbit_state: boolean;
  incidence_angle_delta_deg: number | null;
  warnings: string[];
  scientific_validity: "not_determined";
}

export interface AnalysisSelectionManifest {
  contract_version: "1.0.0";
  selection_id: string;
  created_at: string;
  aoi: { bbox: BBox; geometry: PolygonGeometry };
  aoi_geometry_sha256: string;
  before: CatalogItem;
  after: CatalogItem;
  comparability: ComparabilityEvidence;
  processing_inputs: {
    preset: "echoatlas-standard-v1";
    normalization: "robust-percentile";
    resampling: "bilinear";
    score_method: "absolute-difference";
    score_threshold: number;
    minimum_component_pixels: number;
  };
  interpretation_limits: string[];
  manifest_sha256: string;
}

export interface AnalysisJob {
  contract_version: "1.0.0";
  job_id: string;
  retry_of: string | null;
  status: AnalysisJobStatus;
  manifest: AnalysisSelectionManifest;
  created_at: string;
  updated_at: string;
  error: string | null;
  bundle: unknown;
}

export interface AnalysisJobClient {
  compare(
    aoi: { bbox: BBox; geometry: PolygonGeometry },
    before: CatalogItem,
    after: CatalogItem,
  ): Promise<AnalysisSelectionManifest>;
  start(manifest: AnalysisSelectionManifest): Promise<AnalysisJob>;
  get(jobId: string): Promise<AnalysisJob>;
  cancel(jobId: string): Promise<AnalysisJob>;
  retry(jobId: string, manifestSha256: string): Promise<AnalysisJob>;
}

export class HttpAnalysisJobClient implements AnalysisJobClient {
  constructor(private readonly root = "/api/v1/analysis") {}

  async compare(
    aoi: { bbox: BBox; geometry: PolygonGeometry },
    before: CatalogItem,
    after: CatalogItem,
  ): Promise<AnalysisSelectionManifest> {
    return parseSelectionManifest(
      await this.request(`${this.root}/selections`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          contract_version: "1.0.0",
          aoi,
          before,
          after,
          processing_inputs: { preset: "echoatlas-standard-v1" },
        }),
      }),
    );
  }

  async start(manifest: AnalysisSelectionManifest): Promise<AnalysisJob> {
    return parseAnalysisJob(
      await this.request(`${this.root}/jobs`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ manifest }),
      }),
    );
  }

  async get(jobId: string): Promise<AnalysisJob> {
    return parseAnalysisJob(
      await this.request(`${this.root}/jobs/${encodeURIComponent(jobId)}`),
    );
  }

  async cancel(jobId: string): Promise<AnalysisJob> {
    return parseAnalysisJob(
      await this.request(`${this.root}/jobs/${encodeURIComponent(jobId)}`, {
        method: "DELETE",
      }),
    );
  }

  async retry(jobId: string, manifestSha256: string): Promise<AnalysisJob> {
    return parseAnalysisJob(
      await this.request(
        `${this.root}/jobs/${encodeURIComponent(jobId)}/retry`,
        {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ manifest_sha256: manifestSha256 }),
        },
      ),
    );
  }

  private async request(url: string, init?: RequestInit): Promise<unknown> {
    let response: Response;
    try {
      response = await fetch(url, init);
    } catch (error) {
      throw new Error("The analysis service could not be reached.", {
        cause: error,
      });
    }
    const body: unknown = await response.json().catch(() => null);
    if (!response.ok) {
      const detail =
        isRecord(body) && typeof body.detail === "string"
          ? body.detail
          : `Analysis request failed (${response.status}).`;
      throw new Error(detail);
    }
    return body;
  }
}

export function parseSelectionManifest(
  source: unknown,
): AnalysisSelectionManifest {
  const root = record(source, "selection manifest");
  exact(root.contract_version, "1.0.0", "contract_version");
  const before = catalogItem(root.before, "before");
  const after = catalogItem(root.after, "after");
  const aoi = record(root.aoi, "aoi");
  const geometry = polygon(aoi.geometry, "aoi.geometry");
  const comparability = record(root.comparability, "comparability");
  const processing = record(root.processing_inputs, "processing_inputs");
  const scientificValidity = text(
    comparability.scientific_validity,
    "comparability.scientific_validity",
  );
  if (scientificValidity !== "not_determined") {
    throw invalid("comparability.scientific_validity must be not_determined");
  }
  exact(processing.preset, "echoatlas-standard-v1", "processing_inputs.preset");
  exact(
    processing.normalization,
    "robust-percentile",
    "processing_inputs.normalization",
  );
  exact(processing.resampling, "bilinear", "processing_inputs.resampling");
  exact(
    processing.score_method,
    "absolute-difference",
    "processing_inputs.score_method",
  );
  return {
    contract_version: "1.0.0",
    selection_id: text(root.selection_id, "selection_id"),
    created_at: timestamp(root.created_at, "created_at"),
    aoi: { bbox: bbox(aoi.bbox, "aoi.bbox"), geometry },
    aoi_geometry_sha256: sha256(
      root.aoi_geometry_sha256,
      "aoi_geometry_sha256",
    ),
    before,
    after,
    comparability: {
      temporal_separation_seconds: positive(
        comparability.temporal_separation_seconds,
        "comparability.temporal_separation_seconds",
      ),
      common_footprint: polygon(
        comparability.common_footprint,
        "comparability.common_footprint",
      ),
      common_bbox: bbox(comparability.common_bbox, "comparability.common_bbox"),
      before_overlap_percent: percentage(
        comparability.before_overlap_percent,
        "comparability.before_overlap_percent",
      ),
      after_overlap_percent: percentage(
        comparability.after_overlap_percent,
        "comparability.after_overlap_percent",
      ),
      same_product: boolean(
        comparability.same_product,
        "comparability.same_product",
      ),
      shared_polarizations: texts(
        comparability.shared_polarizations,
        "comparability.shared_polarizations",
      ),
      range_resolution_delta_percent: nonnegative(
        comparability.range_resolution_delta_percent,
        "comparability.range_resolution_delta_percent",
      ),
      azimuth_resolution_delta_percent: nonnegative(
        comparability.azimuth_resolution_delta_percent,
        "comparability.azimuth_resolution_delta_percent",
      ),
      same_observation_direction: boolean(
        comparability.same_observation_direction,
        "comparability.same_observation_direction",
      ),
      same_orbit_state: boolean(
        comparability.same_orbit_state,
        "comparability.same_orbit_state",
      ),
      incidence_angle_delta_deg: nullableNonnegative(
        comparability.incidence_angle_delta_deg,
        "comparability.incidence_angle_delta_deg",
      ),
      warnings: texts(comparability.warnings, "comparability.warnings"),
      scientific_validity: "not_determined",
    },
    processing_inputs: {
      preset: "echoatlas-standard-v1",
      normalization: "robust-percentile",
      resampling: "bilinear",
      score_method: "absolute-difference",
      score_threshold: nonnegative(
        processing.score_threshold,
        "processing_inputs.score_threshold",
      ),
      minimum_component_pixels: integer(
        processing.minimum_component_pixels,
        "processing_inputs.minimum_component_pixels",
      ),
    },
    interpretation_limits: texts(
      root.interpretation_limits,
      "interpretation_limits",
    ),
    manifest_sha256: sha256(root.manifest_sha256, "manifest_sha256"),
  };
}

export function parseAnalysisJob(source: unknown): AnalysisJob {
  const root = record(source, "analysis job");
  exact(root.contract_version, "1.0.0", "contract_version");
  const status = text(root.status, "status");
  if (!jobStatuses.includes(status as AnalysisJobStatus)) {
    throw invalid("status is invalid");
  }
  const bundle = root.bundle ?? null;
  if (bundle !== null && !isRecord(bundle)) {
    throw invalid("bundle must be an object or null");
  }
  return {
    contract_version: "1.0.0",
    job_id: text(root.job_id, "job_id"),
    retry_of: nullableText(root.retry_of, "retry_of"),
    status: status as AnalysisJobStatus,
    manifest: parseSelectionManifest(root.manifest),
    created_at: timestamp(root.created_at, "created_at"),
    updated_at: timestamp(root.updated_at, "updated_at"),
    error: nullableText(root.error, "error"),
    bundle,
  };
}

const jobStatuses: AnalysisJobStatus[] = [
  "queued",
  "running",
  "succeeded",
  "failed",
  "cancelled",
];

function catalogItem(source: unknown, label: string): CatalogItem {
  const root = record(source, label);
  const provider = text(root.provider, `${label}.provider`);
  if (provider !== "umbra" && provider !== "sentinel-1") {
    throw invalid(`${label}.provider is invalid`);
  }
  const license = record(root.license, `${label}.license`);
  const sourceIdentity = record(root.source, `${label}.source`);
  return {
    provider,
    acquired_at: timestamp(root.acquired_at, `${label}.acquired_at`),
    bbox: bbox(root.bbox, `${label}.bbox`),
    footprint: polygon(root.footprint, `${label}.footprint`),
    product_type: nullableText(root.product_type, `${label}.product_type`),
    polarizations: texts(root.polarizations, `${label}.polarizations`),
    resolution_range_m: nullablePositive(
      root.resolution_range_m,
      `${label}.resolution_range_m`,
    ),
    resolution_azimuth_m: nullablePositive(
      root.resolution_azimuth_m,
      `${label}.resolution_azimuth_m`,
    ),
    platform: nullableText(root.platform, `${label}.platform`),
    observation_direction: nullableText(
      root.observation_direction,
      `${label}.observation_direction`,
    ),
    orbit_state: nullableText(root.orbit_state, `${label}.orbit_state`),
    incidence_angle_deg: nullableNonnegative(
      root.incidence_angle_deg,
      `${label}.incidence_angle_deg`,
    ),
    license: {
      label: text(license.label, `${label}.license.label`),
      url: nullableText(license.url, `${label}.license.url`),
    },
    source: {
      item_id: text(sourceIdentity.item_id, `${label}.source.item_id`),
      collection: text(sourceIdentity.collection, `${label}.source.collection`),
      href: text(sourceIdentity.href, `${label}.source.href`),
    },
  };
}

function polygon(source: unknown, label: string): PolygonGeometry {
  const root = record(source, label);
  exact(root.type, "Polygon", `${label}.type`);
  if (!Array.isArray(root.coordinates) || root.coordinates.length === 0) {
    throw invalid(`${label}.coordinates must contain rings`);
  }
  const coordinates = root.coordinates.map((ring, ringIndex) => {
    if (!Array.isArray(ring) || ring.length < 4) {
      throw invalid(`${label}.coordinates[${ringIndex}] is invalid`);
    }
    return ring.map((position, positionIndex) => {
      if (
        !Array.isArray(position) ||
        position.length !== 2 ||
        !position.every((value) => typeof value === "number")
      ) {
        throw invalid(
          `${label}.coordinates[${ringIndex}][${positionIndex}] is invalid`,
        );
      }
      return [position[0], position[1]];
    });
  });
  return { type: "Polygon", coordinates };
}

function bbox(source: unknown, label: string): BBox {
  if (!Array.isArray(source) || source.length !== 4) {
    throw invalid(`${label} must contain four numbers`);
  }
  const values = source.map((value, index) =>
    number(value, `${label}[${index}]`),
  );
  return [values[0], values[1], values[2], values[3]];
}

function record(source: unknown, label: string): Record<string, unknown> {
  if (!isRecord(source)) throw invalid(`${label} must be an object`);
  return source;
}

function isRecord(source: unknown): source is Record<string, unknown> {
  return (
    typeof source === "object" && source !== null && !Array.isArray(source)
  );
}

function exact(source: unknown, expected: string, label: string): void {
  if (source !== expected) throw invalid(`${label} must be ${expected}`);
}

function text(source: unknown, label: string): string {
  if (typeof source !== "string" || source.trim() === "") {
    throw invalid(`${label} must be non-empty text`);
  }
  return source;
}

function nullableText(source: unknown, label: string): string | null {
  return source === null ? null : text(source, label);
}

function texts(source: unknown, label: string): string[] {
  if (!Array.isArray(source)) throw invalid(`${label} must be a list`);
  return source.map((value, index) => text(value, `${label}[${index}]`));
}

function timestamp(source: unknown, label: string): string {
  const value = text(source, label);
  if (Number.isNaN(Date.parse(value))) throw invalid(`${label} is invalid`);
  return value;
}

function number(source: unknown, label: string): number {
  if (typeof source !== "number" || !Number.isFinite(source)) {
    throw invalid(`${label} must be a finite number`);
  }
  return source;
}

function positive(source: unknown, label: string): number {
  const value = number(source, label);
  if (value <= 0) throw invalid(`${label} must be positive`);
  return value;
}

function nonnegative(source: unknown, label: string): number {
  const value = number(source, label);
  if (value < 0) throw invalid(`${label} must be non-negative`);
  return value;
}

function percentage(source: unknown, label: string): number {
  const value = nonnegative(source, label);
  if (value > 100) throw invalid(`${label} must be at most 100`);
  return value;
}

function integer(source: unknown, label: string): number {
  const value = positive(source, label);
  if (!Number.isInteger(value)) throw invalid(`${label} must be an integer`);
  return value;
}

function nullablePositive(source: unknown, label: string): number | null {
  return source === null ? null : positive(source, label);
}

function nullableNonnegative(source: unknown, label: string): number | null {
  return source === null ? null : nonnegative(source, label);
}

function boolean(source: unknown, label: string): boolean {
  if (typeof source !== "boolean") throw invalid(`${label} must be boolean`);
  return source;
}

function sha256(source: unknown, label: string): string {
  const value = text(source, label);
  if (!/^[a-f0-9]{64}$/.test(value)) throw invalid(`${label} must be SHA-256`);
  return value;
}

function invalid(message: string): Error {
  return new Error(`Analysis service returned invalid data: ${message}.`);
}
