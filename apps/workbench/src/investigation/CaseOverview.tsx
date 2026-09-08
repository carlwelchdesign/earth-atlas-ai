import { useEffect, useState } from "react";

import { StateNotice } from "../workbench/Workbench";
import { InvalidInvestigationCaseError, type InvestigationCase } from "./model";
import { SiteHeader } from "./SiteHeader";

function formatDate(value: string) {
  return new Date(value).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC",
  });
}

type OverviewState =
  | { status: "loading" }
  | { status: "ready"; investigation: InvestigationCase }
  | { status: "invalid"; detail: string };

export function CaseOverview({
  loadCase,
}: {
  loadCase: () => Promise<InvestigationCase>;
}) {
  const [state, setState] = useState<OverviewState>({ status: "loading" });
  useEffect(() => {
    let active = true;
    loadCase()
      .then((investigation) => {
        if (active) setState({ status: "ready", investigation });
      })
      .catch((error: unknown) => {
        if (!active) return;
        setState({
          status: "invalid",
          detail:
            error instanceof InvalidInvestigationCaseError
              ? error.message
              : "The prepared investigation could not be loaded.",
        });
      });
    return () => {
      active = false;
    };
  }, [loadCase]);

  if (state.status === "loading") {
    return (
      <div className="investigation-shell">
        <SiteHeader current="case" />
        <main className="load-shell">
          <StateNotice
            kind="loading"
            title="Loading Nepal case"
            message="Validating prepared imagery, coverage, sources, and observations."
          />
        </main>
      </div>
    );
  }
  if (state.status === "invalid") {
    return (
      <div className="investigation-shell">
        <SiteHeader current="case" />
        <main className="load-shell">
          <StateNotice
            kind="error"
            title="Nepal case rejected"
            message={state.detail}
          />
        </main>
      </div>
    );
  }

  const before = state.investigation.acquisitions[0];
  const after = state.investigation.acquisitions[1];
  return (
    <div className="investigation-shell">
      <SiteHeader current="case" />
      <main className="case-overview">
        <section className="case-hero">
          <div>
            <p className="eyebrow">Prepared case · Rasuwa, Nepal</p>
            <h1>Investigate the 2026 Nepal flood corridor</h1>
            <p className="case-question">{state.investigation.question}</p>
            <div className="case-actions">
              <a
                className="primary-button"
                href="/investigate/nepal-flood-2026"
              >
                Start investigation
              </a>
              <span>
                Login-free · browser-local work · deterministic export
              </span>
            </div>
          </div>
          <div
            className="case-hero-imagery"
            aria-label="Prepared before and after preview"
          >
            <figure>
              <img
                src={before.thumbnail}
                alt="Before Sentinel-2 view of the Nepal corridor"
              />
              <figcaption>Before · {formatDate(before.acquiredAt)}</figcaption>
            </figure>
            <figure>
              <img
                src={after.thumbnail}
                alt="After Sentinel-2 view of the Nepal corridor"
              />
              <figcaption>After · {formatDate(after.acquiredAt)}</figcaption>
            </figure>
          </div>
        </section>
        <section className="case-overview-grid">
          <div>
            <p className="eyebrow">Mission</p>
            <h2>Compare. Inspect. Decide.</h2>
            <p>{state.investigation.event.summary}</p>
            <ol>
              <li>
                Choose and navigate two geographically aligned satellite views.
              </li>
              <li>
                Inspect preliminary observations with their original source and
                limits.
              </li>
              <li>
                Record your own assessment separately and export a review brief.
              </li>
            </ol>
          </div>
          <div className="quality-card">
            <p className="eyebrow">Material limitation</p>
            <h2>Cloud obscures part of the after view</h2>
            <p>{state.investigation.quality.summary}</p>
            <details>
              <summary>Read quality and interpretation limits</summary>
              <ul>
                {state.investigation.quality.limitations.map((limitation) => (
                  <li key={limitation}>{limitation}</li>
                ))}
              </ul>
            </details>
          </div>
        </section>
        <section
          className="case-sources"
          aria-labelledby="case-sources-heading"
        >
          <p className="eyebrow">Evidence base</p>
          <h2 id="case-sources-heading">Source identities stay attached</h2>
          <ul>
            {state.investigation.citations.map((citation) => (
              <li key={citation.id}>
                <a href={citation.url} target="_blank" rel="noreferrer">
                  {citation.publisher} · {citation.title}
                </a>
              </li>
            ))}
          </ul>
        </section>
      </main>
    </div>
  );
}
