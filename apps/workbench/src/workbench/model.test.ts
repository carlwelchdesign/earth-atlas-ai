import { describe, expect, it } from "vitest";

import { demoBundle, demoBundleForScenario } from "./demo-bundle";
import { InvalidWorkbenchBundleError, parseWorkbenchBundle } from "./model";

describe("parseWorkbenchBundle", () => {
  it("provides allowlisted recovery-state demo fixtures", () => {
    expect(demoBundleForScenario("stale").freshness.state).toBe("stale");
    expect(demoBundleForScenario("partial").status).toBe("partial");
    expect(
      demoBundleForScenario("permission-denied").permissions.assessments.state,
    ).toBe("denied");
    expect(
      demoBundleForScenario("missing-artifact").acquisitions[1].artifact
        .available,
    ).toBe(false);
    expect(demoBundleForScenario("unknown")).toEqual(demoBundle);
  });
  it("normalizes acquisition order to before then after", () => {
    const bundle = structuredClone(demoBundle);
    bundle.acquisitions.reverse();
    expect(
      parseWorkbenchBundle(bundle).acquisitions.map(({ role }) => role),
    ).toEqual(["before", "after"]);
  });

  it("rejects duplicate candidate IDs", () => {
    const bundle = structuredClone(demoBundle);
    bundle.candidates[1].id = bundle.candidates[0].id;
    expect(() => parseWorkbenchBundle(bundle)).toThrow(
      InvalidWorkbenchBundleError,
    );
  });

  it("rejects non-local artifact paths", () => {
    const bundle = structuredClone(demoBundle);
    bundle.acquisitions[0].artifact.src = "https://example.invalid/image.svg";
    expect(() => parseWorkbenchBundle(bundle)).toThrow("safe local asset path");
  });

  it("accepts satellite-derived PNG assets in the prepared local directory", () => {
    const bundle = structuredClone(demoBundle);
    bundle.acquisitions[0].artifact.mediaType = "image/png";
    bundle.acquisitions[0].artifact.src = "/generated-demo/before.png";
    bundle.evidence.artifacts[0].mediaType = "image/png";
    bundle.evidence.artifacts[0].path = "/generated-demo/before.png";
    bundle.evidence.lineage = "satellite-derived";

    expect(parseWorkbenchBundle(bundle).acquisitions[0].artifact).toMatchObject(
      {
        mediaType: "image/png",
        src: "/generated-demo/before.png",
      },
    );
  });

  it("rejects unsafe evidence links", () => {
    const bundle = structuredClone(demoBundle);
    bundle.evidence.license.href = "javascript:alert(1)";
    expect(() => parseWorkbenchBundle(bundle)).toThrow(
      "unauthenticated HTTPS URL",
    );
  });

  it("rejects evidence links from untrusted hosts", () => {
    const bundle = structuredClone(demoBundle);
    bundle.evidence.license.href = "https://evil.invalid/license";
    expect(() => parseWorkbenchBundle(bundle)).toThrow(
      "host is not allowlisted",
    );
  });

  it("accepts an explicitly unavailable source without a broken href", () => {
    const bundle = structuredClone(demoBundle);
    bundle.evidence.acquisitions[0].source.status = "unavailable";
    bundle.evidence.acquisitions[0].source.href = null;
    expect(
      parseWorkbenchBundle(bundle).evidence.acquisitions[0].source,
    ).toEqual({
      label: "Before fixture",
      href: null,
      status: "unavailable",
    });
  });

  it("rejects duplicate evidence acquisition references", () => {
    const bundle = structuredClone(demoBundle);
    bundle.evidence.acquisitions[1].acquisitionId =
      bundle.evidence.acquisitions[0].acquisitionId;
    expect(() => parseWorkbenchBundle(bundle)).toThrow(
      "duplicate evidence acquisition ID",
    );
  });

  it("rejects candidate references to unknown evidence artifacts", () => {
    const bundle = structuredClone(demoBundle);
    bundle.candidates[0].evidenceArtifactIds.push("artifact-unknown");
    expect(() => parseWorkbenchBundle(bundle)).toThrow(
      "references unknown evidence artifact",
    );
  });

  it("requires reasons for stale freshness and denied assessment permission", () => {
    const stale = structuredClone(demoBundle);
    stale.freshness.state = "stale";
    expect(() => parseWorkbenchBundle(stale)).toThrow(
      "freshness.reason is required",
    );

    const denied = structuredClone(demoBundle);
    denied.permissions.assessments.state = "denied";
    expect(() => parseWorkbenchBundle(denied)).toThrow(
      "permissions.assessments.reason is required",
    );
  });
});
