import { describe, expect, it } from "vitest";

import { lastAllowedCatalogDate, validateCatalogDateRange } from "./model";

describe("catalog date range", () => {
  it("accepts no more than 60 inclusive calendar days", () => {
    expect(() =>
      validateCatalogDateRange("2026-07-27", "2026-09-24"),
    ).not.toThrow();
    expect(() => validateCatalogDateRange("2026-07-27", "2026-09-25")).toThrow(
      "cannot exceed 60 days",
    );
    expect(lastAllowedCatalogDate("2026-07-27")).toBe("2026-09-24");
  });

  it("rejects invalid and reversed ranges", () => {
    expect(() => validateCatalogDateRange("", "2026-08-27")).toThrow(
      "valid acquisition dates",
    );
    expect(() => validateCatalogDateRange("2026-08-27", "2026-08-12")).toThrow(
      "must precede",
    );
  });
});
