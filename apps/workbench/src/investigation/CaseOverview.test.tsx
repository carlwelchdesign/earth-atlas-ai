import { render, screen } from "@testing-library/react";
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
  });
});
