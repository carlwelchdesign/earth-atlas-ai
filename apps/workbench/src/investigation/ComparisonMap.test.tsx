import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { InvestigationCase } from "./model";
import { ComparisonMap } from "./ComparisonMap";
import { copyCamera, isInsideCoverage } from "./map-utils";

const investigation = {
  acquisitions: [
    {
      role: "before",
      acquiredAt: "2026-08-12T05:10:48Z",
      thumbnail: "/generated-nepal/before-thumbnail.png",
    },
    {
      role: "after",
      acquiredAt: "2026-08-27T05:10:45Z",
      thumbnail: "/generated-nepal/after-thumbnail.png",
    },
  ],
  coverage: {
    type: "Polygon",
    coordinates: [
      [
        [85.3, 28.08],
        [85.42, 28.08],
        [85.42, 28.28],
        [85.3, 28.28],
        [85.3, 28.08],
      ],
    ],
  },
  observations: [],
} as unknown as InvestigationCase;

describe("Nepal geographic comparison", () => {
  it("reports whether the camera center is in prepared coverage", () => {
    expect(isInsideCoverage(85.36, 28.18, investigation)).toBe(true);
    expect(isInsideCoverage(86, 29, investigation)).toBe(false);
  });

  it("copies center and zoom without rotation or pitch", () => {
    const target = { jumpTo: vi.fn() };
    const source = {
      getCenter: () => ({ lng: 85.36, lat: 28.18 }),
      getZoom: () => 12,
    };
    copyCamera(source as never, target as never);
    expect(target.jumpTo).toHaveBeenCalledWith({
      center: { lng: 85.36, lat: 28.18 },
      zoom: 12,
      bearing: 0,
      pitch: 0,
    });
  });

  it("provides a static comparison when WebGL is unavailable", () => {
    render(
      <ComparisonMap
        investigation={investigation}
        selectedObservationId={null}
        onSelectObservation={vi.fn()}
        renderMap={false}
      />,
    );
    expect(
      screen.getByLabelText("Static before and after comparison"),
    ).toBeInTheDocument();
    expect(screen.getAllByRole("img")).toHaveLength(2);
    expect(screen.getByRole("status")).toHaveTextContent(
      "Interactive map unavailable",
    );
  });

  it("exposes side-by-side, swipe, and selected-date controls", () => {
    render(
      <ComparisonMap
        investigation={investigation}
        selectedObservationId={null}
        onSelectObservation={vi.fn()}
        renderMap={false}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Swipe" }));
    expect(screen.getByRole("button", { name: "Swipe" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(screen.getByLabelText("After-image reveal")).toHaveValue("50");
    fireEvent.click(screen.getByRole("button", { name: "After" }));
    expect(screen.getByRole("button", { name: "After" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });
});
