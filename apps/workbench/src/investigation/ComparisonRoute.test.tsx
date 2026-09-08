import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import axe from "axe-core";
import { describe, expect, it } from "vitest";

import { ComparisonRoute } from "./ComparisonRoute";
import type { NepalImageryClient } from "./imagery";
import { investigationFixture } from "./test-fixture";

const alternateAfter = {
  ...investigationFixture.acquisitions[1],
  itemId: "S2B_45RUM_20260906_0_L2A",
  productId: "S2B_MSIL2A_20260906_TEST.SAFE",
  acquiredAt: "2026-09-06T05:10:46.120000Z",
  tileTemplate: undefined,
  imageUrl: "/generated-nepal/acquisitions/S2B_45RUM_20260906_0_L2A.png",
  thumbnail: "/generated-nepal/acquisitions/S2B_45RUM_20260906_0_L2A.png",
  checksumSha256: undefined,
  cloudCoverPercent: 77.9,
};

const imagery: NepalImageryClient = {
  listAcquisitions: () => Promise.resolve([alternateAfter]),
};

describe("guided Nepal investigation", () => {
  it("keeps source observations separate from user assessments", async () => {
    render(
      <ComparisonRoute
        loadCase={() => Promise.resolve(investigationFixture)}
        renderMap={false}
        storage={window.localStorage}
        imagery={imagery}
      />,
    );
    expect(
      await screen.findByRole("heading", { name: "Observations" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Published observation")).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Inspect original source" }),
    ).toHaveAttribute("href", investigationFixture.citations[0].url);
    fireEvent.click(screen.getByLabelText("Needs context"));
    fireEvent.change(screen.getByLabelText("Notes"), {
      target: { value: "Cloud obscures the edge." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Record assessment" }));
    expect(await screen.findByText("Assessment recorded.")).toBeInTheDocument();
    expect(screen.getByText("1/2 assessed")).toBeInTheDocument();
    expect(
      screen.getByRole("button", {
        name: /Preliminary reference area 1.*Needs context/,
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Record correction" }),
    ).toBeInTheDocument();
  });

  it("reloads a case-version draft from browser storage", async () => {
    const first = render(
      <ComparisonRoute
        loadCase={() => Promise.resolve(investigationFixture)}
        renderMap={false}
        storage={window.localStorage}
        imagery={imagery}
      />,
    );
    await screen.findByRole("heading", { name: "Observations" });
    fireEvent.click(screen.getByRole("button", { name: "Record assessment" }));
    await screen.findByText("Assessment recorded.");
    first.unmount();
    render(
      <ComparisonRoute
        loadCase={() => Promise.resolve(investigationFixture)}
        renderMap={false}
        storage={window.localStorage}
        imagery={imagery}
      />,
    );
    await waitFor(() =>
      expect(screen.getByText("1/2 assessed")).toBeInTheDocument(),
    );
    expect(
      screen.getByRole("button", { name: "Record correction" }),
    ).toBeInTheDocument();
  });

  it("offers both deterministic brief formats", async () => {
    render(
      <ComparisonRoute
        loadCase={() => Promise.resolve(investigationFixture)}
        renderMap={false}
        storage={window.localStorage}
        imagery={imagery}
      />,
    );

    fireEvent.click(await screen.findByRole("button", { name: /Brief/ }));
    expect(
      screen.getByRole("button", { name: "Download printable HTML" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Download JSON" }),
    ).toBeInTheDocument();
  });

  it("has one quality summary and no automated accessibility violations", async () => {
    render(
      <ComparisonRoute
        loadCase={() => Promise.resolve(investigationFixture)}
        renderMap={false}
        storage={window.localStorage}
        imagery={imagery}
      />,
    );
    await screen.findByRole("heading", { name: "Observations" });
    expect(
      screen.getAllByText("Quality and interpretation limits"),
    ).toHaveLength(1);
    const results = await axe.run(document.body, {
      rules: { "color-contrast": { enabled: false } },
    });
    expect(results.violations).toEqual([]);
  });

  it("updates the georeferenced imagery from an editable acquisition date", async () => {
    render(
      <ComparisonRoute
        loadCase={() => Promise.resolve(investigationFixture)}
        renderMap={false}
        storage={window.localStorage}
        imagery={imagery}
      />,
    );

    const afterDate = await screen.findByLabelText("After imagery date");
    await waitFor(() =>
      expect(
        screen.getByRole("option", { name: /Sep 6, 2026/ }),
      ).toBeInTheDocument(),
    );
    fireEvent.change(afterDate, { target: { value: alternateAfter.itemId } });

    expect(
      await screen.findByText("After imagery updated to Sep 6, 2026."),
    ).toBeInTheDocument();
    expect(
      screen.getByAltText(
        "After Sentinel-2 view of the prepared Nepal corridor",
      ),
    ).toHaveAttribute("src", alternateAfter.imageUrl);
    expect(screen.getByText(/77.9% cloud after/)).toBeInTheDocument();
  });
});
