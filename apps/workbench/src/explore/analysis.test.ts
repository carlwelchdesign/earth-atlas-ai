import { describe, expect, it, vi } from "vitest";

import {
  HttpAnalysisJobClient,
  parseAnalysisJob,
  parseSelectionManifest,
  type AnalysisSelectionManifest,
} from "./analysis";
import { polygonFromBbox, type CatalogItem } from "./model";

const bbox = [-112.2, 40.45, -112.05, 40.6] as const;

function item(role: "before" | "after"): CatalogItem {
  return {
    provider: "umbra",
    acquired_at:
      role === "before" ? "2025-06-10T04:04:46Z" : "2025-07-05T05:18:39Z",
    bbox: [...bbox],
    footprint: polygonFromBbox([...bbox]),
    product_type: "GEC",
    polarizations: ["VV"],
    resolution_range_m: 0.5,
    resolution_azimuth_m: 0.5,
    platform: role === "before" ? "Umbra-05" : "Umbra-08",
    observation_direction: "left",
    orbit_state: "ascending",
    incidence_angle_deg: role === "before" ? 42.1 : 39.9,
    license: {
      label: "CC-BY-4.0",
      url: "https://creativecommons.org/licenses/by/4.0/",
    },
    source: {
      item_id: `umbra-${role}`,
      collection: "umbra-2025",
      href: `https://umbra-open-data-catalog.s3.us-west-2.amazonaws.com/items/umbra-${role}.json`,
    },
  };
}

function manifest(): AnalysisSelectionManifest {
  return {
    contract_version: "1.0.0",
    selection_id: "selection-123",
    created_at: "2026-08-26T02:00:00Z",
    aoi: { bbox: [...bbox], geometry: polygonFromBbox([...bbox]) },
    aoi_geometry_sha256: "a".repeat(64),
    before: item("before"),
    after: item("after"),
    comparability: {
      temporal_separation_seconds: 2_160_000,
      common_footprint: polygonFromBbox([...bbox]),
      common_bbox: [...bbox],
      before_overlap_percent: 99.8,
      after_overlap_percent: 99.7,
      same_product: true,
      shared_polarizations: ["VV"],
      range_resolution_delta_percent: 0,
      azimuth_resolution_delta_percent: 0,
      same_observation_direction: true,
      same_orbit_state: true,
      incidence_angle_delta_deg: 2.2,
      warnings: [],
      scientific_validity: "not_determined",
    },
    processing_inputs: {
      preset: "echoatlas-standard-v1",
      normalization: "robust-percentile",
      resampling: "bilinear",
      score_method: "absolute-difference",
      score_threshold: 0.65,
      minimum_component_pixels: 48,
    },
    interpretation_limits: [
      "Comparability evidence does not establish scientific validity.",
    ],
    manifest_sha256: "b".repeat(64),
  };
}

function response(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

describe("analysis client", () => {
  it("posts comparison before starting a job and preserves the manifest", async () => {
    const selection = manifest();
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(response(selection))
      .mockResolvedValueOnce(
        response(
          {
            contract_version: "1.0.0",
            job_id: "analysis-1",
            retry_of: null,
            status: "queued",
            manifest: selection,
            created_at: "2026-08-26T02:00:00Z",
            updated_at: "2026-08-26T02:00:00Z",
            error: null,
            bundle: null,
          },
          202,
        ),
      );
    const client = new HttpAnalysisJobClient();

    const compared = await client.compare(
      selection.aoi,
      selection.before,
      selection.after,
    );
    const job = await client.start(compared);

    expect(compared.comparability.scientific_validity).toBe("not_determined");
    expect(job.status).toBe("queued");
    expect(fetchMock.mock.calls[0]?.[0]).toBe("/v1/analysis/selections");
    expect(fetchMock.mock.calls[1]?.[0]).toBe("/v1/analysis/jobs");
    const startRequest = fetchMock.mock.calls[1]?.[1];
    const startBody = startRequest?.body;
    if (typeof startBody !== "string") {
      throw new TypeError("analysis job body must be serialized JSON");
    }
    expect(JSON.parse(startBody)).toEqual({
      manifest: selection,
    });
  });

  it("validates untrusted manifest and job data", () => {
    expect(() =>
      parseSelectionManifest({
        ...manifest(),
        comparability: {
          ...manifest().comparability,
          scientific_validity: "valid",
        },
      }),
    ).toThrow(/scientific_validity/);
    expect(() =>
      parseAnalysisJob({
        contract_version: "1.0.0",
        job_id: "analysis-1",
        retry_of: null,
        status: "teleported",
        manifest: manifest(),
        created_at: "2026-08-26T02:00:00Z",
        updated_at: "2026-08-26T02:00:00Z",
        error: null,
        bundle: null,
      }),
    ).toThrow(/status is invalid/);
  });

  it("surfaces a safe server detail", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      response({ detail: "The pair has no polygonal intersection." }, 422),
    );

    await expect(
      new HttpAnalysisJobClient().compare(
        manifest().aoi,
        item("before"),
        item("after"),
      ),
    ).rejects.toThrow("The pair has no polygonal intersection.");
  });
});
