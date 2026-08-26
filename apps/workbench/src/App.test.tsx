import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import axe from "axe-core";
import { afterEach, describe, expect, it, vi } from "vitest";

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

afterEach(() => vi.unstubAllGlobals());

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

  it("keeps Explore and Analyze as reversible peer modes", async () => {
    render(<App loadBundle={load()} />);
    await screen.findByRole("heading", { name: demoBundle.mission.title });

    fireEvent.click(screen.getByRole("button", { name: "Return to Explore" }));
    expect(
      screen.getByRole("heading", {
        name: "Explore provider-reported SAR availability",
      }),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /Analyze/ }));
    expect(
      await screen.findByRole("heading", { name: demoBundle.mission.title }),
    ).toBeInTheDocument();
  });

  it("reports a bounded read-only Foundry connection without relabeling the bundle", async () => {
    render(
      <App
        loadBundle={load()}
        loadPlatformConnection={() =>
          Promise.resolve({
            status: "connected",
            analysisRunAvailable: true,
          })
        }
      />,
    );

    expect(
      await screen.findByText("Palantir read-only · synthetic run available"),
    ).toBeInTheDocument();
    expect(screen.getByText(/no Umbra pixels represented/)).toBeInTheDocument();
  });

  it("keeps the validated local bundle active when Foundry is unavailable", async () => {
    render(
      <App
        loadBundle={load()}
        loadPlatformConnection={() =>
          Promise.reject(new Error("Foundry unavailable"))
        }
      />,
    );

    expect(
      await screen.findByText("Palantir unavailable · local bundle active"),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        level: 1,
        name: demoBundle.mission.title,
      }),
    ).toBeInTheDocument();
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
    expect(
      screen.getByRole("heading", {
        name: "Partial bundle: optional outputs unavailable",
      }),
    ).toBeInTheDocument();
  });

  it("keeps stale evidence usable and records explicit continuation", async () => {
    const bundle = copyBundle();
    bundle.freshness = {
      state: "stale",
      evaluatedAt: "2026-01-20T12:00:00Z",
      reason: "The prepared bundle is older than the review policy window.",
    };
    render(<App loadBundle={load(bundle)} />);

    expect(await screen.findByText("Validated · stale")).toBeInTheDocument();
    expect(
      screen.getByText(/older than the review policy window/),
    ).toBeInTheDocument();
    fireEvent.click(
      screen.getByRole("button", { name: "Continue with stale data" }),
    );
    expect(
      screen.getAllByText(/continuation acknowledged for this session/),
    ).toHaveLength(2);
    expect(
      screen.getByText(
        "Stale bundle continuation acknowledged for this session.",
      ),
    ).toBeInTheDocument();
  });

  it("preserves evidence inspection when assessment permission is denied", async () => {
    const bundle = copyBundle();
    bundle.permissions.assessments = {
      state: "denied",
      reason: "This local role does not have assessment permission.",
    };
    render(<App loadBundle={load(bundle)} />);
    fireEvent.click(
      await screen.findByRole("button", { name: /C-001.*13,000 m²/ }),
    );

    expect(
      screen.getByRole("heading", {
        name: "Assessment permission unavailable",
      }),
    ).toBeInTheDocument();
    expect(screen.getByRole("note")).toHaveTextContent("Read-only inspection");
    expect(
      screen.queryByRole("button", { name: "Record assessment" }),
    ).not.toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Provenance" })).toBeEnabled();
  });

  it("uses a read-only phone path while retaining assessment at 200% zoom equivalent", async () => {
    mockMatchMedia(390);
    const phone = render(<App loadBundle={load()} />);
    fireEvent.click(
      await screen.findByRole("button", { name: /C-001.*13,000 m²/ }),
    );
    expect(screen.getByRole("note")).toHaveTextContent(
      "read-only phone layout",
    );
    expect(
      screen.queryByRole("button", { name: "Record assessment" }),
    ).not.toBeInTheDocument();
    phone.unmount();

    mockMatchMedia(640);
    render(<App loadBundle={load()} />);
    fireEvent.click(
      await screen.findByRole("button", { name: /C-001.*13,000 m²/ }),
    );
    expect(
      screen.getByRole("button", { name: "Record assessment" }),
    ).toBeEnabled();
  });

  it("supports arrow, Home, and End navigation across evidence tabs", async () => {
    render(<App loadBundle={load()} />);
    fireEvent.click(
      await screen.findByRole("button", { name: /C-001.*13,000 m²/ }),
    );
    const review = screen.getByRole("tab", { name: "Review" });
    review.focus();
    fireEvent.keyDown(review, { key: "ArrowRight" });
    expect(screen.getByRole("tab", { name: "Provenance" })).toHaveFocus();
    expect(screen.getByRole("tab", { name: "Provenance" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    fireEvent.keyDown(screen.getByRole("tab", { name: "Provenance" }), {
      key: "End",
    });
    expect(screen.getByRole("tab", { name: "History" })).toHaveFocus();
    fireEvent.keyDown(screen.getByRole("tab", { name: "History" }), {
      key: "Home",
    });
    expect(screen.getByRole("tab", { name: "Review" })).toHaveFocus();
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

  it("restores local assessment history after the workbench remounts", async () => {
    const first = render(<App loadBundle={load()} />);
    fireEvent.click(
      await screen.findByRole("button", { name: /C-001.*13,000 m²/ }),
    );
    fireEvent.click(screen.getByRole("button", { name: "Record assessment" }));
    fireEvent.change(screen.getByLabelText(/Analyst note/), {
      target: { value: "Persist this owner-review decision." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Append assessment" }));
    await screen.findByRole("button", { name: "Correct assessment" });
    first.unmount();

    render(<App loadBundle={load()} />);
    fireEvent.click(
      await screen.findByRole("button", { name: /C-001.*13,000 m²/ }),
    );
    expect(
      await screen.findByRole("button", { name: "Correct assessment" }),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("tab", { name: "History" }));
    expect(
      screen.getByText("Persist this owner-review decision."),
    ).toBeInTheDocument();
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

  it("confirms before discarding a changed assessment draft", async () => {
    render(<App loadBundle={load()} />);
    fireEvent.click(
      await screen.findByRole("button", { name: /C-001.*13,000 m²/ }),
    );
    const invoker = screen.getByRole("button", { name: "Record assessment" });
    fireEvent.click(invoker);
    fireEvent.change(screen.getByLabelText(/Analyst note/), {
      target: { value: "Unsaved review note." },
    });
    fireEvent.keyDown(screen.getByRole("dialog"), { key: "Escape" });

    expect(
      screen.getByRole("heading", {
        name: "Discard unsaved assessment draft?",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Continue editing" }),
    ).toHaveFocus();
    fireEvent.click(screen.getByRole("button", { name: "Continue editing" }));
    expect(screen.getByLabelText(/Analyst note/)).toHaveValue(
      "Unsaved review note.",
    );
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    fireEvent.click(screen.getByRole("button", { name: "Discard draft" }));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    await waitFor(() => expect(invoker).toHaveFocus());
  });

  it("has no automated accessibility violations in the populated workflow", async () => {
    render(<App loadBundle={load()} />);
    fireEvent.click(
      await screen.findByRole("button", { name: /C-001.*13,000 m²/ }),
    );
    const results = await axe.run(document.body, {
      rules: { "color-contrast": { enabled: false } },
    });
    expect(results.violations).toEqual([]);
  });
});

function mockMatchMedia(width: number) {
  vi.stubGlobal(
    "matchMedia",
    vi.fn((query: string) => {
      const maxWidth = /max-width:\s*(\d+)px/.exec(query)?.[1];
      const matches = maxWidth ? width <= Number(maxWidth) : false;
      return {
        matches,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(() => true),
      };
    }),
  );
}
