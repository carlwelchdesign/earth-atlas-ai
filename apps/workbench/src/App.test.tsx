import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { App } from "./App";
import {
  InMemoryAssessmentStore,
  type AssessmentDraft,
  type AssessmentStore,
} from "./workbench/assessment";
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
    ).toBeEnabled();
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

  it("traces a candidate through provenance, processing, warnings, and export", async () => {
    render(<App loadBundle={load()} />);
    fireEvent.click(
      await screen.findByRole("button", { name: /C-001.*13,000 m²/ }),
    );

    expect(
      screen.getByText("Ranking signal from deterministic", { exact: false }),
    ).toHaveTextContent("not calibrated confidence");
    fireEvent.click(screen.getByRole("tab", { name: "Provenance" }));
    expect(screen.getByText("Synthetic lineage")).toBeInTheDocument();
    expect(screen.getAllByText("EchoAtlas fixture generator")).toHaveLength(2);
    expect(
      screen.getByRole("link", { name: "Before fixture" }),
    ).toHaveAttribute("href", "/fixtures/synthetic-before.svg");
    expect(screen.getAllByText(/CC0-1.0/)).toHaveLength(2);

    fireEvent.click(screen.getByRole("tab", { name: "Processing" }));
    expect(screen.getByText("synthetic-change-run-v1")).toBeInTheDocument();
    expect(screen.getByText("echoatlas-workbench 0.1.0")).toBeInTheDocument();
    expect(
      screen.getByText(/Change-score preview is unavailable/),
    ).toBeInTheDocument();

    const download = screen.getByRole("link", { name: "Export evidence JSON" });
    expect(download).toHaveAttribute(
      "download",
      `${demoBundle.bundleId}-C-001-evidence.json`,
    );
    expect(download.getAttribute("href")).toContain("data:application/json");
  });

  it("renders an unavailable external source as text while keeping evidence usable", async () => {
    const bundle = copyBundle();
    bundle.evidence.acquisitions[0].source.status = "unavailable";
    bundle.evidence.acquisitions[0].source.href = null;
    render(<App loadBundle={load(bundle)} />);
    fireEvent.click(
      await screen.findByRole("button", { name: /C-001.*13,000 m²/ }),
    );
    fireEvent.click(screen.getByRole("tab", { name: "Provenance" }));

    expect(
      screen.getByText("Before fixture · source link unavailable"),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("link", { name: "Before fixture" }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "After fixture" }),
    ).toBeInTheDocument();
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

  it("validates and appends an assessment, then filters reviewed and pending candidates", async () => {
    render(<App loadBundle={load()} />);
    fireEvent.click(
      await screen.findByRole("button", { name: /C-001.*13,000 m²/ }),
    );
    fireEvent.click(screen.getByRole("button", { name: "Record assessment" }));
    expect(screen.getByRole("dialog", { name: "C-001" })).toBeInTheDocument();

    fireEvent.click(screen.getByLabelText(/Needs context/));
    fireEvent.click(screen.getByRole("button", { name: "Append assessment" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Add a note describing the context needed",
    );
    fireEvent.change(screen.getByLabelText(/Analyst note/), {
      target: { value: "Confirm whether the apparent edge follows layover." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Retry save" }));

    expect(
      await screen.findByRole("button", { name: "Correct assessment" }),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("tab", { name: "History" }));
    expect(screen.getAllByText("Needs context")).toHaveLength(3);
    expect(screen.getByText("1 event")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Reviewed (1)" }));
    expect(screen.getByRole("list", { name: "Candidates" })).toHaveTextContent(
      "C-001",
    );
    expect(
      screen.getByRole("list", { name: "Candidates" }),
    ).not.toHaveTextContent("C-002");
    fireEvent.click(screen.getByRole("button", { name: "Pending (2)" }));
    expect(
      screen.getByRole("list", { name: "Candidates" }),
    ).not.toHaveTextContent("C-001");
    expect(screen.getByRole("list", { name: "Candidates" })).toHaveTextContent(
      "C-002",
    );
  });

  it("appends a correction while retaining the superseded event", async () => {
    render(<App loadBundle={load()} />);
    fireEvent.click(
      await screen.findByRole("button", { name: /C-002.*8,400 m²/ }),
    );
    fireEvent.click(screen.getByRole("button", { name: "Record assessment" }));
    fireEvent.change(screen.getByLabelText(/Analyst note/), {
      target: { value: "Initial analyst support." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Append assessment" }));
    fireEvent.click(
      await screen.findByRole("button", { name: "Correct assessment" }),
    );

    expect(
      screen.getByText(/will supersede assessment-0001/),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByLabelText(/Rejected/));
    fireEvent.change(screen.getByLabelText(/Analyst note/), {
      target: { value: "Registration review does not support the candidate." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Append assessment" }));

    fireEvent.click(screen.getByRole("tab", { name: "History" }));
    expect(await screen.findByText("2 events")).toBeInTheDocument();
    expect(screen.getByText("Initial analyst support.")).toBeInTheDocument();
    expect(screen.getByText("Superseded")).toBeInTheDocument();
    expect(screen.getByText("Current")).toBeInTheDocument();
    expect(screen.getAllByText("Rejected")).toHaveLength(3);
  });

  it("preserves the assessment draft after a failed save and retries idempotently", async () => {
    const delegate = new InMemoryAssessmentStore({
      candidateIds: demoBundle.candidates.map((candidate) => candidate.id),
    });
    let attempts = 0;
    const store: AssessmentStore = {
      append(draft: AssessmentDraft) {
        attempts += 1;
        if (attempts === 1)
          return Promise.reject(new Error("Local store unavailable."));
        return delegate.append(draft);
      },
    };
    render(<App loadBundle={load()} assessmentStore={store} />);
    fireEvent.click(
      await screen.findByRole("button", { name: /C-003.*5,900 m²/ }),
    );
    fireEvent.click(screen.getByRole("button", { name: "Record assessment" }));
    const note = screen.getByLabelText(/Analyst note/);
    fireEvent.change(note, {
      target: { value: "Retain this draft across failure." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Append assessment" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Local store unavailable",
    );
    expect(note).toHaveValue("Retain this draft across failure.");
    fireEvent.click(screen.getByRole("button", { name: "Retry save" }));
    expect(
      await screen.findByRole("button", { name: "Correct assessment" }),
    ).toBeInTheDocument();
    expect(attempts).toBe(2);
  });

  it("closes the assessment dialog with Escape and restores focus", async () => {
    render(<App loadBundle={load()} />);
    fireEvent.click(
      await screen.findByRole("button", { name: /C-001.*13,000 m²/ }),
    );
    const invoker = screen.getByRole("button", { name: "Record assessment" });
    fireEvent.click(invoker);
    const dialog = screen.getByRole("dialog");
    const close = screen.getByRole("button", { name: "Close assessment" });
    const append = screen.getByRole("button", { name: "Append assessment" });
    close.focus();
    fireEvent.keyDown(dialog, { key: "Tab", shiftKey: true });
    expect(append).toHaveFocus();
    fireEvent.keyDown(dialog, { key: "Tab" });
    expect(close).toHaveFocus();
    fireEvent.keyDown(dialog, { key: "Escape" });
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    await waitFor(() => expect(invoker).toHaveFocus());
  });
});
