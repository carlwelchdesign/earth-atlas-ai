import { describe, expect, it } from "vitest";

import { demoBundle } from "./demo-bundle";
import {
  createCandidateEvidenceExport,
  createEvidenceDownloadHref,
} from "./evidence";

describe("candidate evidence export", () => {
  it("retains attribution, lineage, candidate measurements, and provenance", () => {
    const record = createCandidateEvidenceExport({
      bundle: demoBundle,
      candidate: demoBundle.candidates[0],
      assessments: [],
      exportedAt: "2026-08-25T00:00:00Z",
    });

    expect(record.provenance.attribution).toContain("CC0-1.0");
    expect(record.provenance.lineage).toBe("synthetic-fixture");
    expect(record.candidate.evidenceArtifactIds).toEqual([
      "artifact-before",
      "artifact-after",
    ]);
    expect(record.provenance.acquisitions).toHaveLength(2);
    expect(decodeURIComponent(createEvidenceDownloadHref(record))).toContain(
      '"attribution": "EchoAtlas deterministic synthetic fixture',
    );
  });
});
