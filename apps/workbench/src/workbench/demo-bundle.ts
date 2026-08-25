import type { BundleLoader, WorkbenchBundle } from "./model";

const syntheticBeforeSha256 =
  "8496a287d32b30863111bc632654feb0cd476b09378fcb59795d5f3c3d83257c"; // pragma: allowlist secret
const syntheticAfterSha256 =
  "6e3e6629fa48b3a2e893b02fd3e787cb8ea42af736ae671fbfecdfd8ef3d04ef"; // pragma: allowlist secret

export const demoBundle: WorkbenchBundle = {
  contractVersion: "1.0.0",
  bundleId: "bundle-bingham-canyon-synthetic-v1",
  status: "succeeded",
  createdAt: "2026-01-15T12:00:00Z",
  mission: {
    title: "Bingham Canyon synthetic demonstration",
    boundaryLabel: "Approved review boundary",
  },
  freshness: {
    state: "current",
    evaluatedAt: "2026-01-15T12:00:00Z",
    reason: null,
  },
  permissions: {
    assessments: {
      state: "allowed",
      reason: null,
    },
  },
  acquisitions: [
    {
      id: "acquisition-before-synthetic",
      role: "before",
      acquiredAt: "2025-01-10T12:00:00Z",
      label: "Before",
      artifact: {
        available: true,
        mediaType: "image/svg+xml",
        src: "/fixtures/synthetic-before.svg",
      },
    },
    {
      id: "acquisition-after-synthetic",
      role: "after",
      acquiredAt: "2025-02-10T12:00:00Z",
      label: "After",
      artifact: {
        available: true,
        mediaType: "image/svg+xml",
        src: "/fixtures/synthetic-after.svg",
      },
    },
  ],
  candidates: [
    {
      id: "C-001",
      areaSquareMeters: 13_000,
      pixelCount: 130,
      heuristicScore: 0.92,
      warningCount: 1,
      evidenceArtifactIds: ["artifact-before", "artifact-after"],
      warnings: ["Slope and shadow can create apparent differences."],
      mapPosition: {
        leftPercent: 47,
        topPercent: 39,
        widthPercent: 18,
        heightPercent: 24,
        rotationDegrees: 11,
      },
    },
    {
      id: "C-002",
      areaSquareMeters: 8_400,
      pixelCount: 84,
      heuristicScore: 0.78,
      warningCount: 2,
      evidenceArtifactIds: ["artifact-before", "artifact-after"],
      warnings: [
        "Registration residual may affect this boundary.",
        "Moisture can alter synthetic backscatter-like texture.",
      ],
      mapPosition: {
        leftPercent: 20,
        topPercent: 57,
        widthPercent: 13,
        heightPercent: 17,
        rotationDegrees: -15,
      },
    },
    {
      id: "C-003",
      areaSquareMeters: 5_900,
      pixelCount: 59,
      heuristicScore: 0.66,
      warningCount: 1,
      evidenceArtifactIds: ["artifact-before", "artifact-after"],
      warnings: ["Small components are sensitive to cleanup parameters."],
      mapPosition: {
        leftPercent: 72,
        topPercent: 61,
        widthPercent: 14,
        heightPercent: 16,
        rotationDegrees: 16,
      },
    },
  ],
  qualityWarnings: [],
  evidence: {
    lineage: "synthetic-fixture",
    lineageNotice:
      "The displayed images, measurements, and candidates are deterministic synthetic fixtures. No satellite pixels or satellite-derived measurements are represented.",
    attribution:
      "EchoAtlas deterministic synthetic fixture · CC0-1.0 · no Umbra pixels represented",
    license: {
      label: "CC0 1.0 Universal",
      href: "https://creativecommons.org/publicdomain/zero/1.0/",
      status: "available",
    },
    software: {
      version: "echoatlas-workbench 0.1.0",
      commit: "78b50e0",
    },
    run: {
      id: "synthetic-change-run-v1",
      parameters: [
        { name: "Score threshold", value: "0.60" },
        { name: "Connectivity", value: "8-way" },
        { name: "Minimum component", value: "48 px" },
        { name: "Cleanup", value: "open 1 · close 1" },
      ],
    },
    acquisitions: [
      {
        acquisitionId: "acquisition-before-synthetic",
        provider: "EchoAtlas fixture generator",
        productType: "Synthetic SVG",
        polarization: "Not applicable",
        resolutionMeters: 10,
        incidenceAngleDegrees: 40,
        source: {
          label: "Before fixture",
          href: "/fixtures/synthetic-before.svg",
          status: "available",
        },
        checksum: {
          algorithm: "SHA-256",
          value: syntheticBeforeSha256,
        },
      },
      {
        acquisitionId: "acquisition-after-synthetic",
        provider: "EchoAtlas fixture generator",
        productType: "Synthetic SVG",
        polarization: "Not applicable",
        resolutionMeters: 10,
        incidenceAngleDegrees: 40,
        source: {
          label: "After fixture",
          href: "/fixtures/synthetic-after.svg",
          status: "available",
        },
        checksum: {
          algorithm: "SHA-256",
          value: syntheticAfterSha256,
        },
      },
    ],
    artifacts: [
      {
        id: "artifact-before",
        label: "Before comparison fixture",
        mediaType: "image/svg+xml",
        path: "/fixtures/synthetic-before.svg",
        sha256: syntheticBeforeSha256,
        sizeBytes: 1327,
        required: true,
        available: true,
      },
      {
        id: "artifact-after",
        label: "After comparison fixture",
        mediaType: "image/svg+xml",
        path: "/fixtures/synthetic-after.svg",
        sha256: syntheticAfterSha256,
        sizeBytes: 1489,
        required: true,
        available: true,
      },
      {
        id: "artifact-score-preview",
        label: "Change-score preview",
        mediaType: "image/svg+xml",
        path: "/fixtures/synthetic-score-preview.svg",
        sha256:
          "0000000000000000000000000000000000000000000000000000000000000000",
        sizeBytes: 1,
        required: false,
        available: false,
      },
    ],
    warnings: [
      "Synthetic fixtures demonstrate workflow behavior, not SAR performance.",
      "The optional change-score preview is unavailable in this bundle.",
    ],
  },
};

export const loadDemoBundle: BundleLoader = async () => {
  await Promise.resolve();
  const scenario =
    typeof window === "undefined"
      ? "default"
      : new URLSearchParams(window.location.search).get("fixture");
  return demoBundleForScenario(scenario);
};

export const loadWorkbenchBundle: BundleLoader = async () => {
  const scenario =
    typeof window === "undefined"
      ? null
      : new URLSearchParams(window.location.search).get("fixture");
  if (scenario) return demoBundleForScenario(scenario);
  if (typeof fetch === "undefined") return demoBundleForScenario(null);

  let response: Response;
  try {
    response = await fetch("/generated-demo/bundle.json", {
      cache: "no-store",
    });
  } catch {
    return demoBundleForScenario(null);
  }
  if (response.status === 404) return demoBundleForScenario(null);
  if (!response.ok) {
    throw new Error(
      `Prepared demo request failed with status ${response.status}.`,
    );
  }
  // Static hosts commonly serve the application shell for unknown routes.
  // Treat that HTML fallback as "no prepared bundle" while continuing to
  // reject malformed responses that claim to be JSON.
  const contentType = response.headers.get("content-type")?.toLowerCase() ?? "";
  if (contentType.includes("text/html")) return demoBundleForScenario(null);
  return response.json();
};

export function demoBundleForScenario(scenario: string | null) {
  const bundle = structuredClone(demoBundle);
  if (scenario === "stale") {
    bundle.freshness = {
      state: "stale",
      evaluatedAt: "2026-01-20T12:00:00Z",
      reason: "The prepared bundle is older than the review policy window.",
    };
  } else if (scenario === "partial") {
    bundle.status = "partial";
    bundle.qualityWarnings = [
      "The optional change-score preview is unavailable; comparison and candidate evidence remain usable.",
    ];
  } else if (scenario === "permission-denied") {
    bundle.permissions.assessments = {
      state: "denied",
      reason: "This demonstration role does not have assessment permission.",
    };
  } else if (scenario === "missing-artifact") {
    bundle.acquisitions[1].artifact.available = false;
  }
  return bundle;
}
