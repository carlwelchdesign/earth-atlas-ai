import { useEffect, useMemo, useState, type FormEvent } from "react";

import {
  dispositionLabel,
  type AssessmentDisposition,
  type AssessmentEvent,
} from "../workbench/assessment";
import { StateNotice } from "../workbench/Workbench";
import {
  createInvestigationBrief,
  createInvestigationBriefJson,
  createPrintableInvestigationHtml,
  downloadText,
} from "./brief";
import { CaseAssessmentStore, latestAssessments } from "./case-assessment";
import { ComparisonMap } from "./ComparisonMap";
import {
  HttpNepalImageryClient,
  NEPAL_IMAGERY_WINDOW,
  type NepalImageryClient,
} from "./imagery";
import {
  InvalidInvestigationCaseError,
  type CaseAcquisition,
  loadInvestigationCase,
  type InvestigationCase,
} from "./model";
import { SiteHeader } from "./SiteHeader";

type CaseState =
  | { status: "loading" }
  | { status: "ready"; investigation: InvestigationCase }
  | { status: "invalid"; detail: string };
type InvestigationStep = "context" | "compare" | "review" | "brief";
const defaultNepalImageryClient = new HttpNepalImageryClient();

export function ComparisonRoute({
  loadCase = loadInvestigationCase,
  renderMap = true,
  storage,
  imagery = defaultNepalImageryClient,
}: {
  loadCase?: () => Promise<InvestigationCase>;
  renderMap?: boolean;
  storage?: Storage | null;
  imagery?: NepalImageryClient;
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
      imagery={imagery}
    />
  );
}

function ReadyInvestigation({
  investigation,
  renderMap,
  storage,
  imagery,
}: {
  investigation: InvestigationCase;
  renderMap: boolean;
  storage?: Storage | null;
  imagery: NepalImageryClient;
}) {
  const [step, setStep] = useState<InvestigationStep>("context");
  const [selectedId, setSelectedId] = useState<string | null>(
    investigation.observations[0]?.id ?? null,
  );
  const [events, setEvents] = useState<AssessmentEvent[]>([]);
  const [assessmentMessage, setAssessmentMessage] = useState<string | null>(
    null,
  );
  const [acquisitions, setAcquisitions] = useState<
    [CaseAcquisition, CaseAcquisition]
  >(investigation.acquisitions);
  const [availableAcquisitions, setAvailableAcquisitions] = useState<
    CaseAcquisition[]
  >([...investigation.acquisitions]);
  const [imageryStatus, setImageryStatus] = useState(
    "Loading available Sentinel-2 dates…",
  );
  const [imageryAttempt, setImageryAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    void imagery
      .listAcquisitions(
        NEPAL_IMAGERY_WINDOW.start,
        NEPAL_IMAGERY_WINDOW.end,
        controller.signal,
      )
      .then((results) => {
        const prepared = new Map(
          investigation.acquisitions.map((acquisition) => [
            acquisition.itemId,
            acquisition,
          ]),
        );
        const merged = results.map(
          (acquisition) => prepared.get(acquisition.itemId) ?? acquisition,
        );
        for (const acquisition of investigation.acquisitions) {
          if (
            !merged.some((candidate) => candidate.itemId === acquisition.itemId)
          ) {
            merged.push(acquisition);
          }
        }
        merged.sort((left, right) =>
          left.acquiredAt.localeCompare(right.acquiredAt),
        );
        setAvailableAcquisitions(merged);
        setImageryStatus(
          `${merged.length} Sentinel-2 acquisitions available in the 60-day case window.`,
        );
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        setImageryStatus(
          error instanceof Error
            ? `${error.message} The prepared pair remains available.`
            : "Available dates could not be loaded. The prepared pair remains available.",
        );
      });
    return () => controller.abort();
  }, [imagery, imageryAttempt, investigation.acquisitions]);
  const eventDate = investigation.event.occurredAt;
  const beforeOptions = availableAcquisitions.filter(
    (acquisition) => acquisition.acquiredAt.slice(0, 10) < eventDate,
  );
  const afterOptions = availableAcquisitions.filter(
    (acquisition) => acquisition.acquiredAt.slice(0, 10) > eventDate,
  );
  const activeInvestigation = useMemo<InvestigationCase>(() => {
    const [before, after] = acquisitions;
    const dynamicSelection =
      before.imageUrl !== undefined || after.imageUrl !== undefined;
    return {
      ...investigation,
      acquisitions,
      quality: {
        ...investigation.quality,
        summary: `Selected source tiles report ${before.cloudCoverPercent.toFixed(1)}% cloud before and ${after.cloudCoverPercent.toFixed(1)}% cloud after. These are full-tile metadata values; inspect the visible corridor directly.`,
        limitations: [
          `The selected scenes report ${before.cloudCoverPercent.toFixed(1)}% and ${after.cloudCoverPercent.toFixed(1)}% cloud cover across their full Sentinel-2 tiles, not the case AOI alone.`,
          ...(dynamicSelection
            ? [
                "Updated views are rendered on demand from public georeferenced Sentinel-2 visual COGs.",
              ]
            : []),
          ...investigation.quality.limitations.filter(
            (limitation) =>
              !limitation.startsWith("The after scene reports") &&
              !limitation.startsWith("Panning changes location only"),
          ),
          "Panning changes location only; changing a date explicitly replaces that fixed acquisition.",
        ],
      },
    };
  }, [acquisitions, investigation]);
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
  const brief = useMemo(
    () => createInvestigationBrief(activeInvestigation, events),
    [activeInvestigation, events],
  );

  function exportJson() {
    downloadText(
      `${investigation.caseId}-brief.json`,
      createInvestigationBriefJson(brief),
      "application/json;charset=utf-8",
    );
  }

  function exportHtml() {
    downloadText(
      `${investigation.caseId}-brief.html`,
      createPrintableInvestigationHtml(brief, window.location.origin),
      "text/html;charset=utf-8",
    );
  }

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
          <div
            className="fixed-dates editable-dates"
            aria-label="Acquisition dates"
          >
            <label>
              Before
              <select
                aria-label="Before imagery date"
                value={acquisitions[0].itemId}
                onChange={(event) => {
                  const selected = beforeOptions.find(
                    (candidate) =>
                      candidate.itemId === event.currentTarget.value,
                  );
                  if (!selected) return;
                  setAcquisitions([
                    { ...selected, role: "before" },
                    acquisitions[1],
                  ]);
                  setImageryStatus(
                    `Before imagery updated to ${formatDate(selected.acquiredAt)}.`,
                  );
                }}
              >
                {beforeOptions.map((acquisition) => (
                  <option key={acquisition.itemId} value={acquisition.itemId}>
                    {formatDate(acquisition.acquiredAt)} ·{" "}
                    {acquisition.cloudCoverPercent.toFixed(1)}% tile cloud
                  </option>
                ))}
              </select>
            </label>
            <label>
              After
              <select
                aria-label="After imagery date"
                value={acquisitions[1].itemId}
                onChange={(event) => {
                  const selected = afterOptions.find(
                    (candidate) =>
                      candidate.itemId === event.currentTarget.value,
                  );
                  if (!selected) return;
                  setAcquisitions([
                    acquisitions[0],
                    { ...selected, role: "after" },
                  ]);
                  setImageryStatus(
                    `After imagery updated to ${formatDate(selected.acquiredAt)}.`,
                  );
                }}
              >
                {afterOptions.map((acquisition) => (
                  <option key={acquisition.itemId} value={acquisition.itemId}>
                    {formatDate(acquisition.acquiredAt)} ·{" "}
                    {acquisition.cloudCoverPercent.toFixed(1)}% tile cloud
                  </option>
                ))}
              </select>
            </label>
            <button
              type="button"
              className="date-refresh"
              onClick={() => {
                setImageryStatus("Loading available Sentinel-2 dates…");
                setImageryAttempt((attempt) => attempt + 1);
              }}
            >
              Refresh dates
            </button>
            <small role="status" aria-live="polite">
              {imageryStatus}
            </small>
            <small className="imagery-attribution">
              Contains modified Copernicus Sentinel data (2026), accessed
              through Element 84 Earth Search.
            </small>
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
              <div className="brief-panel">
                <div>
                  <p className="eyebrow">Brief</p>
                  <h2>
                    {events.length} assessment event
                    {events.length === 1 ? "" : "s"} ready
                  </h2>
                  <p>
                    {investigation.observations.length - latest.size}{" "}
                    observations remain unresolved. Both formats contain the
                    same source and assessment record.
                  </p>
                </div>
                <div className="brief-actions">
                  <button
                    type="button"
                    className="primary-button"
                    onClick={exportHtml}
                  >
                    Download printable HTML
                  </button>
                  <button
                    type="button"
                    className="secondary-button"
                    onClick={exportJson}
                  >
                    Download JSON
                  </button>
                </div>
              </div>
            ) : null}
            <ComparisonMap
              investigation={activeInvestigation}
              selectedObservationId={selectedId}
              onSelectObservation={selectObservation}
              renderMap={renderMap}
            />
            <details className="investigation-quality">
              <summary>Quality and interpretation limits</summary>
              <p>{activeInvestigation.quality.summary}</p>
              <ul>
                {activeInvestigation.quality.limitations.map((limitation) => (
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

function formatDate(timestamp: string) {
  return new Date(timestamp).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC",
  });
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
