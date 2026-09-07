import { useEffect, useMemo, useState, type FormEvent } from "react";

import {
  dispositionLabel,
  type AssessmentDisposition,
  type AssessmentEvent,
} from "../workbench/assessment";
import { StateNotice } from "../workbench/Workbench";
import { CaseAssessmentStore, latestAssessments } from "./case-assessment";
import { ComparisonMap } from "./ComparisonMap";
import {
  InvalidInvestigationCaseError,
  loadInvestigationCase,
  type InvestigationCase,
} from "./model";
import { SiteHeader } from "./SiteHeader";

type CaseState =
  | { status: "loading" }
  | { status: "ready"; investigation: InvestigationCase }
  | { status: "invalid"; detail: string };
type InvestigationStep = "context" | "compare" | "review" | "brief";

export function ComparisonRoute({
  loadCase = loadInvestigationCase,
  renderMap = true,
  storage,
}: {
  loadCase?: () => Promise<InvestigationCase>;
  renderMap?: boolean;
  storage?: Storage | null;
}) {
  const [state, setState] = useState<CaseState>({ status: "loading" });
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
        <SiteHeader current="investigate" />
        <main className="load-shell">
          <StateNotice
            kind="loading"
            title="Loading Nepal investigation"
            message="Validating the case, sources, coverage, observations, and prepared imagery paths."
          />
        </main>
      </div>
    );
  }
  if (state.status === "invalid") {
    return (
      <div className="investigation-shell">
        <SiteHeader current="investigate" />
        <main className="load-shell">
          <StateNotice
            kind="error"
            title="Investigation rejected"
            message={state.detail}
          />
        </main>
      </div>
    );
  }
  return (
    <ReadyInvestigation
      investigation={state.investigation}
      renderMap={renderMap}
      storage={storage}
    />
  );
}

function ReadyInvestigation({
  investigation,
  renderMap,
  storage,
}: {
  investigation: InvestigationCase;
  renderMap: boolean;
  storage?: Storage | null;
}) {
  const [step, setStep] = useState<InvestigationStep>("context");
  const [selectedId, setSelectedId] = useState<string | null>(
    investigation.observations[0]?.id ?? null,
  );
  const [events, setEvents] = useState<AssessmentEvent[]>([]);
  const [assessmentMessage, setAssessmentMessage] = useState<string | null>(
    null,
  );
  const store = useMemo(
    () =>
      new CaseAssessmentStore({
        caseId: investigation.caseId,
        caseVersion: investigation.caseVersion,
        observationIds: investigation.observations.map(
          (observation) => observation.id,
        ),
        storage,
      }),
    [investigation, storage],
  );
  useEffect(() => {
    void store.load().then(setEvents);
  }, [store]);
  const latest = latestAssessments(events);
  const selected =
    investigation.observations.find(
      (observation) => observation.id === selectedId,
    ) ?? null;
  const citation = selected
    ? (investigation.citations.find(
        (entry) => entry.id === selected.citationId,
      ) ?? null)
    : null;

  function selectObservation(id: string) {
    setSelectedId(id);
    setStep("review");
  }

  return (
    <div className="investigation-shell">
      <SiteHeader current="investigate" />
      <main className="guided-investigation">
        <header className="investigation-titlebar">
          <div>
            <p className="eyebrow">Prepared case · {investigation.location}</p>
            <h1>{investigation.title}</h1>
            <p>{investigation.question}</p>
          </div>
          <div className="fixed-dates" aria-label="Fixed acquisition dates">
            <span>
              Before<strong>12 Aug 2026</strong>
            </span>
            <span>
              After<strong>27 Aug 2026</strong>
            </span>
          </div>
        </header>
        <nav className="investigation-steps" aria-label="Investigation steps">
          {(["context", "compare", "review", "brief"] as const).map(
            (item, index) => (
              <button
                type="button"
                key={item}
                aria-current={step === item ? "step" : undefined}
                onClick={() => setStep(item)}
              >
                <span>{index + 1}</span>
                {item[0].toUpperCase() + item.slice(1)}
              </button>
            ),
          )}
        </nav>
        <div className="investigation-layout">
          <section className="investigation-main">
            {step === "context" ? (
              <div className="step-intro">
                <p className="eyebrow">Context</p>
                <h2>Start with the source boundary</h2>
                <p>{investigation.event.summary}</p>
                <button
                  type="button"
                  className="primary-button"
                  onClick={() => setStep("compare")}
                >
                  Compare imagery
                </button>
              </div>
            ) : null}
            {step === "brief" ? (
              <div className="step-intro">
                <p className="eyebrow">Brief</p>
                <h2>{events.length} assessment events ready</h2>
                <p>
                  {investigation.observations.length - latest.size} observations
                  remain unresolved. Export controls follow in the brief step.
                </p>
              </div>
            ) : null}
            <ComparisonMap
              investigation={investigation}
              selectedObservationId={selectedId}
              onSelectObservation={selectObservation}
              renderMap={renderMap}
            />
            <details className="investigation-quality">
              <summary>Quality and interpretation limits</summary>
              <p>{investigation.quality.summary}</p>
              <ul>
                {investigation.quality.limitations.map((limitation) => (
                  <li key={limitation}>{limitation}</li>
                ))}
              </ul>
            </details>
          </section>
          <aside
            className="observation-rail"
            aria-labelledby="observations-heading"
          >
            <div className="observation-heading">
              <p className="eyebrow">Source-reported</p>
              <h2 id="observations-heading">Observations</h2>
              <span>
                {latest.size}/{investigation.observations.length} assessed
              </span>
            </div>
            <div className="observation-list">
              {investigation.observations.map((observation, index) => {
                const assessment = latest.get(observation.id);
                return (
                  <button
                    type="button"
                    key={observation.id}
                    aria-label={`${index + 1}. ${observation.title}. ${assessment ? dispositionLabel(assessment.disposition) : "Unresolved"}`}
                    aria-current={
                      selectedId === observation.id ? "true" : undefined
                    }
                    onClick={() => selectObservation(observation.id)}
                  >
                    <span>{String(index + 1).padStart(2, "0")}</span>
                    <strong>{observation.title}</strong>
                    <small>
                      {assessment
                        ? dispositionLabel(assessment.disposition)
                        : "Unresolved"}
                    </small>
                  </button>
                );
              })}
            </div>
            {selected && citation ? (
              <ObservationEvidence
                key={`${selected.id}:${latest.get(selected.id)?.eventId ?? "new"}`}
                observation={selected}
                citation={citation}
                current={latest.get(selected.id) ?? null}
                store={store}
                onSaved={setEvents}
                onAnnounce={setAssessmentMessage}
              />
            ) : null}
          </aside>
        </div>
        <p className="storage-note" role="status">
          {store.persistenceAvailable
            ? "Draft assessments are stored only in this browser and case version."
            : "Browser storage is unavailable. Current in-memory assessments remain exportable until this page closes."}
        </p>
        {assessmentMessage ? (
          <p className="assessment-announcement" role="status">
            {assessmentMessage}
          </p>
        ) : null}
      </main>
    </div>
  );
}

function ObservationEvidence({
  observation,
  citation,
  current,
  store,
  onSaved,
  onAnnounce,
}: {
  observation: InvestigationCase["observations"][number];
  citation: InvestigationCase["citations"][number];
  current: AssessmentEvent | null;
  store: CaseAssessmentStore;
  onSaved: (events: AssessmentEvent[]) => void;
  onAnnounce: (message: string) => void;
}) {
  const [disposition, setDisposition] = useState<AssessmentDisposition>(
    current?.disposition ?? "supported",
  );
  const [note, setNote] = useState(current?.note ?? "");
  const [error, setError] = useState<string | null>(null);

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    try {
      await store.append({
        requestId:
          globalThis.crypto?.randomUUID?.() ?? `assessment-${Date.now()}`,
        candidateId: observation.id,
        disposition,
        note,
        ...(current ? { supersedesEventId: current.eventId } : {}),
      });
      onSaved(await store.load());
      onAnnounce(current ? "Correction appended." : "Assessment recorded.");
    } catch (error: unknown) {
      setError(
        error instanceof Error
          ? error.message
          : "Assessment could not be recorded.",
      );
    }
  }

  return (
    <section
      className="observation-evidence"
      aria-labelledby="selected-observation-heading"
    >
      <p className="evidence-kicker">Published observation</p>
      <h3 id="selected-observation-heading">{observation.title}</h3>
      <p>{observation.statement}</p>
      <dl>
        <div>
          <dt>Publisher</dt>
          <dd>{citation.publisher}</dd>
        </div>
        <div>
          <dt>Reference</dt>
          <dd>{observation.evidenceReference}</dd>
        </div>
      </dl>
      <a href={citation.url} target="_blank" rel="noreferrer">
        Inspect original source
      </a>
      <ul className="evidence-limitations">
        {observation.limitations.map((limitation) => (
          <li key={limitation}>{limitation}</li>
        ))}
      </ul>
      <form
        className="observation-assessment"
        onSubmit={(event) => void save(event)}
      >
        <fieldset>
          <legend>Your assessment</legend>
          <label>
            <input
              type="radio"
              name={`disposition-${observation.id}`}
              checked={disposition === "supported"}
              onChange={() => setDisposition("supported")}
            />
            Supported by cited evidence
          </label>
          <label>
            <input
              type="radio"
              name={`disposition-${observation.id}`}
              checked={disposition === "rejected"}
              onChange={() => setDisposition("rejected")}
            />
            Not supported
          </label>
          <label>
            <input
              type="radio"
              name={`disposition-${observation.id}`}
              checked={disposition === "needs-context"}
              onChange={() => setDisposition("needs-context")}
            />
            Needs context
          </label>
        </fieldset>
        <label className="assessment-note">
          Notes
          <textarea
            value={note}
            maxLength={500}
            rows={3}
            onChange={(event) => setNote(event.currentTarget.value)}
          />
        </label>
        <button className="primary-button" type="submit">
          {current ? "Record correction" : "Record assessment"}
        </button>
        {current ? (
          <small>
            Correction will supersede {current.eventId}; history remains intact.
          </small>
        ) : null}
        {error ? <p role="alert">{error}</p> : null}
      </form>
    </section>
  );
}
