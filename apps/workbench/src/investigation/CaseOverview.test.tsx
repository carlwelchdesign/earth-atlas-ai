import { render, screen } from "@testing-library/react";
import axe from "axe-core";
import { describe, expect, it } from "vitest";

import { CaseOverview } from "./CaseOverview";
import { investigationFixture } from "./test-fixture";

describe("Nepal case overview", () => {
  it("makes the investigation the primary action", async () => {
    render(
      <CaseOverview loadCase={() => Promise.resolve(investigationFixture)} />,
    );
    expect(
      await screen.findByRole("heading", {
        name: "Investigate the 2026 Nepal flood corridor",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Start investigation" }),
    ).toHaveAttribute("href", "/investigate/nepal-flood-2026");
    expect(
      screen.getByText("Cloud obscures part of the after view."),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /UNOSAT/ })).toHaveAttribute(
      "href",
      investigationFixture.citations[0].url,
    );
    expect(
      screen.getAllByText("Cloud obscures part of the after view."),
    ).toHaveLength(1);
  });

  it("has no automated accessibility violations", async () => {
    render(
      <CaseOverview loadCase={() => Promise.resolve(investigationFixture)} />,
    );
    await screen.findByRole("link", { name: "Start investigation" });
    const results = await axe.run(document.body, {
      rules: { "color-contrast": { enabled: false } },
    });
    expect(results.violations).toEqual([]);
  });
});
