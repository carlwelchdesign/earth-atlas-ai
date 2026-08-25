import type { BundleLoader, WorkbenchBundle } from "./model";

export const demoBundle: WorkbenchBundle = {
  contractVersion: "1.0.0",
  bundleId: "bundle-bingham-canyon-synthetic-v1",
  status: "succeeded",
  createdAt: "2026-01-15T12:00:00Z",
  mission: {
    title: "Bingham Canyon synthetic demonstration",
    boundaryLabel: "Approved review boundary",
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
};

export const loadDemoBundle: BundleLoader = async () => {
  await Promise.resolve();
  return demoBundle;
};
