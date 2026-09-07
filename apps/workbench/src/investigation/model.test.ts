import { describe, expect, it } from "vitest";

import { InvalidInvestigationCaseError, parseInvestigationCase } from "./model";

const validCase = {
  contractVersion: "1.0.0",
  caseId: "nepal-flood-2026",
  caseVersion: "1.0.0",
  title: "Nepal flood investigation",
  location: "Rasuwa, Nepal",
  question: "What does the cited evidence support?",
  event: {
    occurredAt: "2026-08-26",
    summary: "A flash flood affected the corridor.",
  },
  aoi: {
    type: "Polygon",
    coordinates: [
      [
        [85.3, 28.08],
        [85.42, 28.08],
        [85.42, 28.28],
        [85.3, 28.08],
      ],
    ],
  },
  coverage: {
    type: "Polygon",
    coordinates: [
      [
        [85.3, 28.08],
        [85.42, 28.08],
        [85.42, 28.28],
        [85.3, 28.08],
      ],
    ],
  },
  acquisitions: [
    {
      role: "before",
      itemId: "before",
      productId: "before-product",
      acquiredAt: "2026-08-12T05:10:48Z",
      tileTemplate: "/generated-nepal/tiles/before/{z}/{x}/{y}.png",
      thumbnail: "/generated-nepal/before-thumbnail.png",
      sourceUrl:
        "https://earth-search.aws.element84.com/v1/collections/sentinel-2-l2a/items/before",
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
        "https://earth-search.aws.element84.com/v1/collections/sentinel-2-l2a/items/after",
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
      id: "extent-1",
      title: "Reference extent",
      statement: "UNOSAT mapped a preliminary extent.",
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [85.3, 28.08],
            [85.31, 28.08],
            [85.31, 28.09],
            [85.3, 28.08],
          ],
        ],
      },
      focus: [85.305, 28.085],
      evidenceReference: "Feature 1",
      citationId: "unosat",
      limitations: ["Not field validated."],
    },
  ],
  attribution: ["Copernicus Sentinel data 2026"],
  quality: {
    summary: "Cloud obscures parts of the after image.",
    limitations: ["Visual conclusions are limited in cloud."],
    alignmentToleranceMetres: 10,
    measuredGridResidualMetres: [0, 0, 0, 0, 0],
  },
  preparedAt: "2026-09-07T00:00:00Z",
  preparation: {
    command: "python scripts/prepare_nepal_case.py",
    sourceManifest: "/generated-nepal/source-manifest.json",
  },
};

describe("investigation case contract", () => {
  it("accepts a separately versioned prepared case", () => {
    expect(parseInvestigationCase(validCase)).toMatchObject({
      contractVersion: "1.0.0",
      caseId: "nepal-flood-2026",
    });
  });

  it("rejects undeclared evidence references", () => {
    const candidate = structuredClone(validCase);
    candidate.observations[0].citationId = "missing";
    expect(() => parseInvestigationCase(candidate)).toThrow(
      InvalidInvestigationCaseError,
    );
  });

  it("rejects remote and traversal asset paths", () => {
    for (const path of [
      "https://example.com/tile.png",
      "/generated-nepal/../secret",
    ]) {
      const candidate = structuredClone(validCase);
      candidate.acquisitions[0].thumbnail = path;
      expect(() => parseInvestigationCase(candidate)).toThrow(
        "approved local asset path",
      );
    }
  });

  it("rejects evidence hosts outside the narrow allowlist", () => {
    const candidate = structuredClone(validCase);
    candidate.citations[0].url = "https://example.com/report";
    expect(() => parseInvestigationCase(candidate)).toThrow(
      "unapproved evidence host",
    );
  });

  it("leaves the existing SAR bundle contract independent", () => {
    const candidate = structuredClone(validCase);
    candidate.contractVersion = "2.0.0";
    expect(() => parseInvestigationCase(candidate)).toThrow("must be 1.0.0");
  });
});
