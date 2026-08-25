import { describe, expect, it } from "vitest";

import { demoBundle } from "./demo-bundle";
import { InvalidWorkbenchBundleError, parseWorkbenchBundle } from "./model";

describe("parseWorkbenchBundle", () => {
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
    expect(() => parseWorkbenchBundle(bundle)).toThrow(
      "safe local fixture path",
    );
  });
});
