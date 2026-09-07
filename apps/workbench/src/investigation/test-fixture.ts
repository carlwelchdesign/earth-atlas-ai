import type { InvestigationCase } from "./model";

const area = {
  type: "Polygon" as const,
  coordinates: [
    [
      [85.3, 28.08] as [number, number],
      [85.42, 28.08] as [number, number],
      [85.42, 28.28] as [number, number],
      [85.3, 28.28] as [number, number],
      [85.3, 28.08] as [number, number],
    ],
  ],
};

export const investigationFixture: InvestigationCase = {
  contractVersion: "1.0.0",
  caseId: "nepal-flood-2026",
  caseVersion: "1.0.0",
  title: "Nepal flood investigation",
  location: "Rasuwa, Nepal",
  question: "What does the cited evidence support?",
  event: {
    occurredAt: "2026-08-26",
    summary: "A flash flood affected the prepared river corridor.",
  },
  aoi: area,
  coverage: area,
  acquisitions: [
    {
      role: "before",
      itemId: "before",
      productId: "before-product",
      acquiredAt: "2026-08-12T05:10:48Z",
      tileTemplate: "/generated-nepal/tiles/before/{z}/{x}/{y}.png",
      thumbnail: "/generated-nepal/before-thumbnail.png",
      sourceUrl:
        "https://earth-search.aws.element84.com/v1/collections/x/items/before",
      checksumSha256: "a".repeat(64),
      crs: "EPSG:32645",
      resolutionMetres: 10,
      cloudCoverPercent: 18,
      cloudShadowPercent: 1,
      nodataPercent: 9,
    },
    {
      role: "after",
      itemId: "after",
      productId: "after-product",
      acquiredAt: "2026-08-27T05:10:45Z",
      tileTemplate: "/generated-nepal/tiles/after/{z}/{x}/{y}.png",
      thumbnail: "/generated-nepal/after-thumbnail.png",
      sourceUrl:
        "https://earth-search.aws.element84.com/v1/collections/x/items/after",
      checksumSha256: "b".repeat(64),
      crs: "EPSG:32645",
      resolutionMetres: 10,
      cloudCoverPercent: 78,
      cloudShadowPercent: 1,
      nodataPercent: 9,
    },
  ],
  citations: [
    {
      id: "unosat",
      publisher: "UNOSAT",
      title: "Preliminary extent",
      url: "https://ihp-wins.unesco.org/dataset/example",
      accessedAt: "2026-09-07",
    },
  ],
  observations: [
    {
      id: "observation-1",
      title: "Preliminary reference area 1",
      statement: "UNOSAT mapped this preliminary reference geometry.",
      geometry: area,
      focus: [85.36, 28.18],
      evidenceReference: "Feature 1",
      citationId: "unosat",
      limitations: ["Not field validated."],
    },
    {
      id: "observation-2",
      title: "Preliminary reference area 2",
      statement: "UNOSAT mapped a second preliminary reference geometry.",
      geometry: area,
      focus: [85.35, 28.15],
      evidenceReference: "Feature 2",
      citationId: "unosat",
      limitations: ["Not field validated."],
    },
  ],
  attribution: ["Contains modified Copernicus Sentinel data (2026)."],
  quality: {
    summary: "Cloud obscures part of the after view.",
    limitations: ["Conclusions are limited to visible areas."],
    alignmentToleranceMetres: 10,
    measuredGridResidualMetres: [0, 0, 0, 0, 0],
  },
  preparedAt: "2026-09-07T00:00:00Z",
  preparation: {
    command: "python scripts/prepare_nepal_case.py",
    sourceManifest: "/generated-nepal/source-manifest.json",
  },
};
