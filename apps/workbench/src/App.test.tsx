import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { App } from "./App";
import { demoBundle } from "./workbench/demo-bundle";

const load =
  (bundle: unknown = demoBundle) =>
  () =>
    Promise.resolve(bundle);
const copyBundle = () => structuredClone(demoBundle);

describe("App", () => {
  it("shows a validation state while the bundle is loading", () => {
    render(<App loadBundle={() => new Promise(() => undefined)} />);
    expect(
      screen.getByRole("heading", { name: "Validating bundle" }),
    ).toBeInTheDocument();
  });

  it("renders a successful, bounded temporal comparison", async () => {
    render(<App loadBundle={load()} />);
    expect(
      await screen.findByRole("heading", {
        level: 1,
        name: demoBundle.mission.title,
      }),
    ).toBeInTheDocument();
    expect(screen.getByText("Validated bundle")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Interpretation boundary" }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Map legend")).toHaveTextContent(
      "Approved boundary",
    );
    fireEvent.click(screen.getByRole("button", { name: /C-001.*13,000 m²/ }));
    expect(
      screen.getByRole("button", { name: "Record assessment" }),
    ).toBeDisabled();
  });

  it("keeps queue and map selection synchronized", async () => {
    render(<App loadBundle={load()} />);
    const queueCandidate = await screen.findByRole("button", {
      name: /C-001.*13,000 m²/,
    });
    fireEvent.click(queueCandidate);
    expect(queueCandidate).toHaveAttribute("aria-current", "true");
    expect(screen.getByRole("heading", { name: "C-001" })).toBeInTheDocument();

    fireEvent.click(
      screen.getByRole("button", {
        name: "Select candidate C-002 on Before map",
      }),
    );
    expect(screen.getByRole("heading", { name: "C-002" })).toBeInTheDocument();
    expect(
      screen.getByText(
        "Candidate C-002 selected. Comparison and evidence updated.",
      ),
    ).toBeInTheDocument();
  });

  it("switches views, synchronizes zoom, and preserves the non-map candidate route", async () => {
    render(<App loadBundle={load()} />);
    await screen.findByRole("heading", { name: demoBundle.mission.title });

    fireEvent.click(screen.getByRole("button", { name: "After" }));
    expect(screen.getByRole("button", { name: "After" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    const comparison = screen.getByRole("region", {
      name: /^After synthetic image comparison/,
    });
    expect(
      within(comparison).queryByText("10 Jan 2025"),
    ).not.toBeInTheDocument();
    expect(within(comparison).getByText("10 Feb 2025")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Zoom in both views" }));
    expect(screen.getByText("View scale 120%")).toBeInTheDocument();

    fireEvent.click(
      screen.getByRole("checkbox", { name: "Candidate overlay" }),
    );
    expect(
      screen.queryByRole("button", { name: /Select candidate C-001 on/ }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /C-001.*13,000 m²/ }),
    ).toBeInTheDocument();
  });

  it("shows the explicit empty-candidate state without hiding the comparison", async () => {
    const bundle = copyBundle();
    bundle.candidates = [];
    render(<App loadBundle={load(bundle)} />);
    expect(
      await screen.findByRole("heading", { name: "No change candidates" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("region", { name: /synthetic image comparison/ }),
    ).toBeInTheDocument();
  });

  it("fails closed when the contract version is invalid", async () => {
    const bundle = { ...copyBundle(), contractVersion: "2.0.0" };
    render(<App loadBundle={load(bundle)} />);
    expect(
      await screen.findByRole("heading", { name: "Bundle rejected" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent(
      "No artifacts were rendered",
    );
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
  });

  it("keeps available evidence visible when a required artifact is missing", async () => {
    const bundle = copyBundle();
    bundle.acquisitions[1].artifact.available = false;
    render(<App loadBundle={load(bundle)} />);
    expect(
      await screen.findByRole("heading", {
        name: "Required comparison artifact is missing",
      }),
    ).toBeInTheDocument();
    expect(screen.getByText("After imagery unavailable")).toBeInTheDocument();
    expect(screen.getByText("Required artifact missing")).toBeInTheDocument();
  });

  it("surfaces quality warnings without presenting them as a successful bundle", async () => {
    const bundle = copyBundle();
    bundle.status = "partial";
    bundle.qualityWarnings = [
      "Synthetic registration residual exceeds the review threshold.",
    ];
    render(<App loadBundle={load(bundle)} />);
    expect(
      await screen.findByText("Validated with warnings"),
    ).toBeInTheDocument();
    expect(screen.getAllByText(bundle.qualityWarnings[0])).toHaveLength(2);
  });
});
