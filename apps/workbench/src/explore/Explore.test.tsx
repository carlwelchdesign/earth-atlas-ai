import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { App } from "../App";
import type { CatalogSearchClient } from "./catalog";
import {
  polygonFromBbox,
  type CatalogItem,
  type CatalogSearchRequest,
  type CatalogSearchResponse,
} from "./model";

const sentinel: CatalogItem = {
  provider: "sentinel-1",
  acquired_at: "2025-07-20T11:00:00Z",
  bbox: [-112.2, 40.45, -112.05, 40.6],
  footprint: polygonFromBbox([-112.2, 40.45, -112.05, 40.6]),
  product_type: "GRD",
  polarizations: ["VV", "VH"],
  resolution_range_m: 10,
  resolution_azimuth_m: 10,
  platform: "Sentinel-1A",
  observation_direction: "right",
  orbit_state: "descending",
  incidence_angle_deg: 38,
  license: { label: "Copernicus Data Space notice", url: null },
  source: {
    item_id: "S1-2025-07-20",
    collection: "sentinel-1-grd",
    href: "https://example.test/sentinel",
  },
};

const umbra: CatalogItem = {
  ...sentinel,
  provider: "umbra",
  acquired_at: "2025-07-28T08:30:00Z",
  product_type: "GEC",
  polarizations: ["HH"],
  resolution_range_m: 0.5,
  platform: "Umbra",
  source: {
    item_id: "UMBRA-2025-07-28",
    collection: "umbra-open-data",
    href: "https://example.test/umbra",
  },
};

function response(
  results: CatalogItem[] = [umbra, sentinel],
): CatalogSearchResponse {
  return {
    contract_version: "1.0.0",
    query_id: "query-test",
    status: results.length ? "complete" : "empty",
    generated_at: "2025-08-25T00:00:00Z",
    cache: "miss",
    results,
    providers: [
      {
        provider: "sentinel-1",
        status: "complete",
        result_count: results.filter((item) => item.provider === "sentinel-1")
          .length,
        has_more: false,
        warning_count: 0,
      },
      {
        provider: "umbra",
        status: "complete",
        result_count: results.filter((item) => item.provider === "umbra")
          .length,
        has_more: false,
        warning_count: 0,
      },
    ],
    warnings: [],
    next_cursor: null,
    sampled_result_count: results.length,
  };
}

function client(result = response()): CatalogSearchClient {
  return {
    search: vi.fn((request: CatalogSearchRequest) => {
      const selectedProviders = new Set(request.providers);
      const results = result.results.filter((item) =>
        selectedProviders.has(item.provider),
      );
      return Promise.resolve({
        ...result,
        results,
        providers: result.providers.filter((report) =>
          selectedProviders.has(report.provider),
        ),
        warnings: result.warnings.filter(
          (warning) =>
            warning.provider === null ||
            selectedProviders.has(warning.provider),
        ),
        sampled_result_count: results.length,
      });
    }),
  };
}

describe("Explore", () => {
  it("keeps the map supplementary and searches the provider-neutral catalog", async () => {
    const catalog = client();
    render(
      <App initialMode="explore" catalog={catalog} renderExploreMap={false} />,
    );

    expect(
      screen.getByText("The globe is navigation—not imagery coverage."),
    ).toBeInTheDocument();
    fireEvent.click(
      screen.getByRole("button", { name: "Search reported acquisitions" }),
    );

    expect(
      await screen.findByRole("heading", { name: "2 reported acquisitions" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("region", {
        name: /Every acquisition remains available/,
      }),
    ).toBeInTheDocument();
    expect(catalog.search).toHaveBeenNthCalledWith(
      1,
      expect.objectContaining({
        contract_version: "1.0.0",
        providers: ["umbra"],
      }),
      expect.any(AbortSignal),
    );
    expect(catalog.search).toHaveBeenNthCalledWith(
      2,
      expect.objectContaining({ providers: ["sentinel-1"] }),
      expect.any(AbortSignal),
    );
    expect(
      screen.queryByText("2 Sentinel-1 · 2 Umbra"),
    ).not.toBeInTheDocument();
    expect(screen.getByText("1 Umbra · 1 Sentinel-1")).toBeInTheDocument();
  });

  it("supports list-only pair selection and blocks the same acquisition in both slots", async () => {
    render(
      <App initialMode="explore" catalog={client()} renderExploreMap={false} />,
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Search reported acquisitions" }),
    );
    await screen.findByRole("heading", { name: "2 reported acquisitions" });

    fireEvent.click(
      screen.getByRole("button", { name: "Use UMBRA-2025-07-28 as Before" }),
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Use UMBRA-2025-07-28 as After" }),
    );
    expect(screen.getByRole("alert")).toHaveTextContent(
      "Choose two distinct acquisitions",
    );

    fireEvent.click(
      screen.getByRole("button", { name: "Use S1-2025-07-20 as After" }),
    );
    const tray = screen
      .getByRole("heading", { name: "Candidate pair" })
      .closest("aside");
    expect(tray).not.toBeNull();
    const reviewButton = within(tray!).getByRole("button", {
      name: "Review pair",
    });
    expect(reviewButton).toBeEnabled();
    expect(
      within(tray!).getByText(
        "Machine-selected inputs, not a valid scientific pair.",
      ),
    ).toBeInTheDocument();

    fireEvent.click(reviewButton);
    const dialog = screen.getByRole("dialog", {
      name: "Review candidate pair",
    });
    expect(
      screen.getByRole("heading", { name: "Review candidate pair" }),
    ).toHaveFocus();
    expect(
      within(dialog).getByText("UMBRA-2025-07-28", { exact: false }),
    ).toBeInTheDocument();
    expect(
      within(dialog).getByRole("button", { name: /Check comparability/ }),
    ).toBeDisabled();
    fireEvent.keyDown(dialog, { key: "Escape" });
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(reviewButton).toHaveFocus();
  });

  it("distinguishes an empty provider response from never-imaged", async () => {
    render(
      <App
        initialMode="explore"
        catalog={client(response([]))}
        renderExploreMap={false}
      />,
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Search reported acquisitions" }),
    );
    expect(
      await screen.findByRole("heading", {
        name: "No provider reported coverage for this query",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/does not mean the area was never imaged/i),
    ).toBeInTheDocument();
  });

  it("preserves a successful provider when another provider fails", async () => {
    const partialClient: CatalogSearchClient = {
      search: vi.fn((request: CatalogSearchRequest) =>
        request.providers[0] === "umbra"
          ? Promise.reject(new Error("bounded timeout"))
          : Promise.resolve({
              ...response([sentinel]),
              providers: [
                {
                  provider: "sentinel-1" as const,
                  status: "complete" as const,
                  result_count: 1,
                  has_more: false,
                  warning_count: 0,
                },
              ],
            }),
      ),
    };
    render(
      <App
        initialMode="explore"
        catalog={partialClient}
        renderExploreMap={false}
      />,
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Search reported acquisitions" }),
    );

    expect(
      await screen.findByRole("heading", { name: "1 reported acquisition" }),
    ).toBeInTheDocument();
    expect(screen.getByText("failed · 0 records")).toBeInTheDocument();
    expect(screen.getByText(/Umbra did not complete/)).toBeInTheDocument();
    expect(screen.getByText(/Sentinel-1 ·/)).toBeInTheDocument();
  });

  it("marks existing results stale when a filter changes", async () => {
    render(
      <App initialMode="explore" catalog={client()} renderExploreMap={false} />,
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Search reported acquisitions" }),
    );
    await screen.findByRole("heading", { name: "2 reported acquisitions" });
    fireEvent.change(screen.getByLabelText("Product"), {
      target: { value: "GRD" },
    });
    expect(
      screen.getByText("Results are stale for this draft"),
    ).toBeInTheDocument();
  });

  it("validates AOI limits before making another provider call", () => {
    const catalog = client();
    render(
      <App initialMode="explore" catalog={catalog} renderExploreMap={false} />,
    );
    fireEvent.change(screen.getByLabelText("West, south, east, north"), {
      target: { value: "-120, 30, -110, 40" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Apply exact AOI" }));
    expect(screen.getByRole("alert")).toHaveTextContent(
      "25-square-degree limit",
    );
    expect(catalog.search).not.toHaveBeenCalled();
  });

  it("offers a pointer AOI mode with an Escape exit and exact-coordinate fallback", () => {
    render(
      <App initialMode="explore" catalog={client()} renderExploreMap={false} />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Draw AOI on map" }));
    expect(screen.getByRole("status")).toHaveTextContent(
      "Select two opposite corners",
    );
    expect(
      screen.getByLabelText("West, south, east, north"),
    ).toBeInTheDocument();

    fireEvent.keyDown(window, { key: "Escape" });
    expect(
      screen.queryByText("Select two opposite corners"),
    ).not.toBeInTheDocument();
  });
});
