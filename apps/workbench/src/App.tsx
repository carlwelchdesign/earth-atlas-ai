import { useCallback, useEffect, useState } from "react";

import { loadWorkbenchBundle } from "./workbench/demo-bundle";
import type { AssessmentStore } from "./workbench/assessment";
import {
  InvalidWorkbenchBundleError,
  parseWorkbenchBundle,
  type BundleLoader,
  type WorkbenchBundle,
} from "./workbench/model";
import { StateNotice, Workbench } from "./workbench/Workbench";

type LoadState =
  | { status: "loading" }
  | { status: "ready"; bundle: WorkbenchBundle }
  | { status: "invalid"; detail: string };

export function App({
  loadBundle = loadWorkbenchBundle,
  assessmentStore,
}: {
  loadBundle?: BundleLoader;
  assessmentStore?: AssessmentStore;
}) {
  const [attempt, setAttempt] = useState(0);
  const [state, setState] = useState<LoadState>({ status: "loading" });

  useEffect(() => {
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
  }, [loadBundle, attempt]);

  const retry = useCallback(() => {
    setState({ status: "loading" });
    setAttempt((current) => current + 1);
  }, []);

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

  return <Workbench bundle={state.bundle} assessmentStore={assessmentStore} />;
}
