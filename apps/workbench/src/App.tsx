import { useCallback, useEffect, useState } from "react";

import { loadWorkbenchBundle } from "./workbench/demo-bundle";
import type { AssessmentStore } from "./workbench/assessment";
import {
  InvalidWorkbenchBundleError,
  parseWorkbenchBundle,
  type BundleLoader,
  type WorkbenchBundle,
} from "./workbench/model";
import {
  initialPlatformConnectionState,
  loadPalantirConnectionState,
  type PlatformConnectionState,
} from "./workbench/palantir";
import { StateNotice, Workbench } from "./workbench/Workbench";
import { Explore } from "./explore/Explore";
import type {
  CatalogSearchClient,
  PlaceSearchAdapter,
} from "./explore/catalog";
import type { BasemapConfig } from "./explore/basemap";
import type { AnalysisJobClient } from "./explore/analysis";

type LoadState =
  | { status: "loading" }
  | { status: "ready"; bundle: WorkbenchBundle }
  | { status: "invalid"; detail: string };

export function App({
  loadBundle = loadWorkbenchBundle,
  loadPlatformConnection = loadPalantirConnectionState,
  assessmentStore,
  initialMode = "analyze",
  catalog,
  places,
  analysis,
  basemap,
  renderExploreMap = true,
  analysisPollMs = 750,
}: {
  loadBundle?: BundleLoader;
  loadPlatformConnection?: () => Promise<PlatformConnectionState>;
  assessmentStore?: AssessmentStore;
  initialMode?: "explore" | "analyze";
  catalog?: CatalogSearchClient;
  places?: PlaceSearchAdapter;
  analysis?: AnalysisJobClient;
  basemap?: BasemapConfig;
  renderExploreMap?: boolean;
  analysisPollMs?: number;
}) {
  const [mode, setMode] = useState(initialMode);
  const [attempt, setAttempt] = useState(0);
  const [state, setState] = useState<LoadState>({ status: "loading" });
  const [analysisBundle, setAnalysisBundle] = useState<WorkbenchBundle | null>(
    null,
  );
  const [platformConnection, setPlatformConnection] =
    useState<PlatformConnectionState>(initialPlatformConnectionState);

  useEffect(() => {
    if (mode === "explore") return;
    if (analysisBundle) return;
    let active = true;
    loadBundle()
      .then((source) => parseWorkbenchBundle(source))
      .then((bundle) => {
        if (active) setState({ status: "ready", bundle });
      })
      .catch((error: unknown) => {
        if (!active) return;
        const detail =
          error instanceof InvalidWorkbenchBundleError
            ? error.message
            : "The bundle source could not be loaded.";
        setState({ status: "invalid", detail });
      });
    return () => {
      active = false;
    };
  }, [analysisBundle, loadBundle, attempt, mode]);

  useEffect(() => {
    if (mode === "explore") return;
    let active = true;
    loadPlatformConnection()
      .then((connection) => {
        if (active) setPlatformConnection(connection);
      })
      .catch(() => {
        if (active)
          setPlatformConnection({
            status: "unavailable",
            reason:
              "The read-only Foundry check did not complete. The validated local bundle remains active.",
          });
      });
    return () => {
      active = false;
    };
  }, [loadPlatformConnection, mode]);

  const retry = useCallback(() => {
    setState({ status: "loading" });
    setAttempt((current) => current + 1);
  }, []);

  const openAnalysisBundle = useCallback((bundle: WorkbenchBundle) => {
    const validated = parseWorkbenchBundle(bundle);
    setAnalysisBundle(validated);
    setState({ status: "ready", bundle: validated });
    setMode("analyze");
  }, []);

  if (mode === "explore") {
    return (
      <Explore
        onAnalyze={() => setMode("analyze")}
        onAnalysisReady={openAnalysisBundle}
        catalog={catalog}
        places={places}
        analysis={analysis}
        basemap={basemap}
        renderMap={renderExploreMap}
        analysisPollMs={analysisPollMs}
      />
    );
  }

  if (state.status === "loading") {
    return (
      <main className="load-shell">
        <div className="load-brand">
          <span aria-hidden="true">EA</span>
          <strong>EchoAtlas</strong>
        </div>
        <StateNotice
          kind="loading"
          title="Validating bundle"
          message="Checking the contract version, required fields, local artifact paths, and comparison records."
        />
      </main>
    );
  }

  if (state.status === "invalid") {
    return (
      <main className="load-shell">
        <div className="load-brand">
          <span aria-hidden="true">EA</span>
          <strong>EchoAtlas</strong>
        </div>
        <StateNotice
          kind="error"
          title="Bundle rejected"
          message={`No artifacts were rendered. ${state.detail}`}
          action="Retry bundle"
          onAction={retry}
        />
      </main>
    );
  }

  return (
    <Workbench
      key={state.bundle.bundleId}
      bundle={state.bundle}
      platformConnection={platformConnection}
      assessmentStore={assessmentStore}
      onExplore={() => setMode("explore")}
    />
  );
}
