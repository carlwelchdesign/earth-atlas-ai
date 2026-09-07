import { describe, expect, it } from "vitest";

import type { AssessmentEvent } from "../workbench/assessment";
import {
  createInvestigationBrief,
  createInvestigationBriefJson,
  createPrintableInvestigationHtml,
} from "./brief";
import { investigationFixture } from "./test-fixture";

const events: AssessmentEvent[] = [
  {
    requestId: "request-1",
    bundleId: "nepal-flood-2026@1.0.0",
    candidateId: "observation-1",
    disposition: "supported",
    note: "Initial view",
    eventId: "assessment-0001",
    createdAt: "2026-09-07T12:00:00.000Z",
  },
  {
    requestId: "request-2",
    bundleId: "nepal-flood-2026@1.0.0",
    candidateId: "observation-1",
    disposition: "needs-context",
    note: '<script>alert("escape me")</script>',
    supersedesEventId: "assessment-0001",
    eventId: "assessment-0002",
    createdAt: "2026-09-07T12:01:00.000Z",
  },
];

describe("investigation brief", () => {
  it("derives matching assessment, unresolved, source, and date records", () => {
    const brief = createInvestigationBrief(investigationFixture, events);
    const json = JSON.parse(
      createInvestigationBriefJson(brief),
    ) as typeof brief;

    expect(json.acquisitions.map((entry) => entry.acquiredAt)).toEqual(
      investigationFixture.acquisitions.map((entry) => entry.acquiredAt),
    );
    expect(json.observations[0].assessment?.label).toBe("Needs context");
    expect(json.observations[0].assessmentHistory).toHaveLength(2);
    expect(json.unresolvedObservationIds).toEqual(["observation-2"]);
    expect(json.citations.map((citation) => citation.id)).toContain(
      json.observations[0].citationId,
    );
  });

  it("escapes user text and includes prepared thumbnails in printable HTML", () => {
    const brief = createInvestigationBrief(investigationFixture, events);
    const html = createPrintableInvestigationHtml(
      brief,
      "https://atlas.example",
    );

    expect(html).not.toContain('<script>alert("escape me")</script>');
    expect(html).toContain(
      "&lt;script&gt;alert(&quot;escape me&quot;)&lt;/script&gt;",
    );
    expect(html).toContain(
      "https://atlas.example/generated-nepal/before-thumbnail.png",
    );
    expect(html).toContain(investigationFixture.acquisitions[1].acquiredAt);
    expect(html).toContain("No model generated this brief.");
  });

  it("is deterministic for identical inputs", () => {
    const brief = createInvestigationBrief(investigationFixture, events);
    expect(createInvestigationBriefJson(brief)).toBe(
      createInvestigationBriefJson(brief),
    );
    expect(
      createPrintableInvestigationHtml(brief, "https://atlas.example"),
    ).toBe(createPrintableInvestigationHtml(brief, "https://atlas.example"));
  });
});
