import { useEffect, useState } from "react";

import { ComparisonMap } from "./ComparisonMap";
import {
  InvalidInvestigationCaseError,
  loadInvestigationCase,
  type InvestigationCase,
} from "./model";
import { StateNotice } from "../workbench/Workbench";

type CaseState =
  | { status: "loading" }
  | { status: "ready"; investigation: InvestigationCase }
  | { status: "invalid"; detail: string };

export function ComparisonRoute({
  loadCase = loadInvestigationCase,
  renderMap = true,
}: {
  loadCase?: () => Promise<InvestigationCase>;
  renderMap?: boolean;
}) {
  const [state, setState] = useState<CaseState>({ status: "loading" });
  const [selectedObservationId, setSelectedObservationId] = useState<
    string | null
  >(null);

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
      <main className="load-shell">
        <StateNotice
          kind="loading"
          title="Loading Nepal investigation"
          message="Validating the case, sources, coverage, observations, and prepared imagery paths."
        />
      </main>
    );
  }
  if (state.status === "invalid") {
    return (
      <main className="load-shell">
        <StateNotice
          kind="error"
          title="Investigation rejected"
          message={state.detail}
        />
      </main>
    );
  }
  return (
    <main className="investigation-comparison-route">
      <header>
        <p className="eyebrow">Prepared investigation · Rasuwa, Nepal</p>
        <h1>{state.investigation.title}</h1>
        <p>{state.investigation.question}</p>
      </header>
      <ComparisonMap
        investigation={state.investigation}
        selectedObservationId={selectedObservationId}
        onSelectObservation={setSelectedObservationId}
        renderMap={renderMap}
      />
    </main>
  );
}
