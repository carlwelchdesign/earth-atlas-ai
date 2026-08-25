import {
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
  type CSSProperties,
  type KeyboardEvent,
} from "react";

import {
  AssessmentDialog,
  type AssessmentDialogValue,
} from "./AssessmentDialog";
import {
  InMemoryAssessmentStore,
  dispositionLabel,
  type AssessmentDraft,
  type AssessmentEvent,
  type AssessmentStore,
} from "./assessment";
import {
  createCandidateEvidenceExport,
  createEvidenceDownloadHref,
} from "./evidence";

import type {
  AcquisitionView,
  CandidateView,
  ComparisonMode,
  WorkbenchBundle,
} from "./model";

interface WorkbenchProps {
  bundle: WorkbenchBundle;
  assessmentStore?: AssessmentStore;
}

const zoomLevels = [1, 1.2, 1.4] as const;
let assessmentRequestSequence = 0;

export function Workbench({ bundle, assessmentStore }: WorkbenchProps) {
  const [selectedCandidateId, setSelectedCandidateId] = useState<string | null>(
    null,
  );
  const [comparisonMode, setComparisonMode] =
    useState<ComparisonMode>(getInitialMode);
  const [overlayVisible, setOverlayVisible] = useState(true);
  const [zoomIndex, setZoomIndex] = useState(0);
  const [assessmentEvents, setAssessmentEvents] = useState<AssessmentEvent[]>(
    [],
  );
  const [assessmentDialog, setAssessmentDialog] =
    useState<AssessmentDialogValue | null>(null);
  const [assessmentAnnouncement, setAssessmentAnnouncement] = useState("");
  const [staleAccepted, setStaleAccepted] = useState(false);
  const compactReadOnly = useMediaQuery("(max-width: 479px)");
  const assessmentInvoker = useRef<HTMLElement | null>(null);
  const [localAssessmentStore] = useState(
    () =>
      new InMemoryAssessmentStore({
        candidateIds: bundle.candidates.map((candidate) => candidate.id),
      }),
  );
  const activeAssessmentStore = assessmentStore ?? localAssessmentStore;
  const currentAssessments = useMemo(
    () => currentAssessmentMap(assessmentEvents),
    [assessmentEvents],
  );
  const selectedCandidate =
    bundle.candidates.find(
      (candidate) => candidate.id === selectedCandidateId,
    ) ?? null;
  const missingAcquisitions = bundle.acquisitions.filter(
    (acquisition) => !acquisition.artifact.available,
  );
  const degraded =
    bundle.status === "partial" || bundle.qualityWarnings.length > 0;
  const stale = bundle.freshness.state === "stale";
  const status =
    missingAcquisitions.length > 0
      ? "missing"
      : stale
        ? "stale"
        : degraded
          ? "degraded"
          : "success";
  const assessmentUnavailableReason = compactReadOnly
    ? "Assessment actions are unavailable in the read-only phone layout. Use a viewport at least 480 CSS pixels wide to record an assessment."
    : bundle.permissions.assessments.state === "denied"
      ? bundle.permissions.assessments.reason
      : null;
  const zoom = zoomLevels[zoomIndex];

  function closeAssessmentDialog() {
    setAssessmentDialog(null);
    queueMicrotask(() => assessmentInvoker.current?.focus());
  }

  function openAssessmentDialog(candidateId: string, invoker: HTMLElement) {
    assessmentInvoker.current = invoker;
    setAssessmentDialog({
      requestId: createAssessmentRequestId(),
      candidateId,
      currentEvent: currentAssessments.get(candidateId) ?? null,
    });
  }

  async function saveAssessment(draft: AssessmentDraft) {
    const event = await activeAssessmentStore.append(draft);
    setAssessmentEvents((current) =>
      current.some((item) => item.eventId === event.eventId)
        ? current
        : [...current, event],
    );
    setAssessmentAnnouncement(
      `${dispositionLabel(event.disposition)} assessment appended for ${event.candidateId}.`,
    );
    closeAssessmentDialog();
  }

  function selectCandidate(candidateId: string) {
    setSelectedCandidateId(candidateId);
    setAssessmentAnnouncement("");
  }

  useEffect(() => {
    if (typeof window.matchMedia !== "function") return;
    const media = window.matchMedia("(max-width: 767px)");
    const synchronize = (event: MediaQueryListEvent | MediaQueryList) => {
      if (event.matches)
        setComparisonMode((mode) => (mode === "two-up" ? "before" : mode));
    };
    media.addEventListener("change", synchronize);
    synchronize(media);
    return () => media.removeEventListener("change", synchronize);
  }, []);

  const selectionAnnouncement = selectedCandidate
    ? `Candidate ${selectedCandidate.id} selected. Comparison and evidence updated.`
    : "No candidate selected.";

  return (
    <div
      className="workbench-shell"
      data-bundle-state={status}
      data-mode={comparisonMode}
    >
      <a className="skip-link" href="#candidate-queue">
        Skip to candidate queue
      </a>
      <MissionHeader bundle={bundle} status={status} />
      <QualityBanner bundle={bundle} status={status} />
      {stale ? (
        <StateNotice
          kind="warning"
          title="Stale bundle"
          message={`${bundle.freshness.reason} Evaluated ${formatTimestamp(bundle.freshness.evaluatedAt)}.${staleAccepted ? " Stale data continuation acknowledged for this session." : " Review remains available; verify freshness before relying on the evidence."}`}
          action={staleAccepted ? undefined : "Continue with stale data"}
          onAction={() => {
            setStaleAccepted(true);
            setAssessmentAnnouncement(
              "Stale bundle continuation acknowledged for this session.",
            );
          }}
        />
      ) : null}
      {status === "missing" ? (
        <StateNotice
          kind="warning"
          title="Required comparison artifact is missing"
          message={`${missingAcquisitions.map((item) => item.label).join(" and ")} imagery is unavailable. Available evidence remains visible, but the comparison is incomplete.`}
        />
      ) : null}
      {bundle.status === "partial" ? (
        <StateNotice
          kind="warning"
          title="Partial bundle: optional outputs unavailable"
          message={
            bundle.qualityWarnings[0] ?? "An optional output is unavailable."
          }
        />
      ) : degraded ? (
        <StateNotice
          kind="warning"
          title="Validated bundle with quality warnings"
          message={bundle.qualityWarnings[0]}
        />
      ) : null}
      {bundle.permissions.assessments.state === "denied" ? (
        <StateNotice
          kind="warning"
          title="Assessment permission unavailable"
          message={`${bundle.permissions.assessments.reason} Evidence inspection remains available.`}
        />
      ) : null}
      <main className="workbench-grid" aria-label="Analyst workbench">
        <CandidateQueue
          candidates={bundle.candidates}
          currentAssessments={currentAssessments}
          selectedCandidateId={selectedCandidateId}
          onSelect={selectCandidate}
        />
        <TemporalComparison
          acquisitions={bundle.acquisitions}
          boundaryLabel={bundle.mission.boundaryLabel}
          candidates={bundle.candidates}
          comparisonMode={comparisonMode}
          onComparisonModeChange={setComparisonMode}
          overlayVisible={overlayVisible}
          onOverlayVisibleChange={setOverlayVisible}
          selectedCandidateId={selectedCandidateId}
          onCandidateSelect={selectCandidate}
          zoom={zoom}
          zoomIndex={zoomIndex}
          onZoomIn={() =>
            setZoomIndex((index) => Math.min(index + 1, zoomLevels.length - 1))
          }
          onZoomOut={() => setZoomIndex((index) => Math.max(index - 1, 0))}
          onReset={() => setZoomIndex(0)}
        />
        <CandidateSummary
          bundle={bundle}
          candidate={selectedCandidate}
          events={assessmentEvents.filter(
            (event) => event.candidateId === selectedCandidateId,
          )}
          currentEvent={
            selectedCandidateId
              ? (currentAssessments.get(selectedCandidateId) ?? null)
              : null
          }
          assessmentUnavailableReason={assessmentUnavailableReason}
          onStartAssessment={openAssessmentDialog}
        />
      </main>
      <footer className="workbench-footer">
        <span>{bundle.evidence.attribution}</span>
        <span>Bundle contract {bundle.contractVersion}</span>
      </footer>
      <div className="sr-status" role="status" aria-live="polite">
        {assessmentAnnouncement || selectionAnnouncement}
      </div>
      {assessmentDialog ? (
        <AssessmentDialog
          bundleId={bundle.bundleId}
          value={assessmentDialog}
          onCancel={closeAssessmentDialog}
          onSave={saveAssessment}
        />
      ) : null}
    </div>
  );
}

interface MissionHeaderProps {
  bundle: WorkbenchBundle;
  status: "success" | "degraded" | "missing" | "stale";
}

function MissionHeader({ bundle, status }: MissionHeaderProps) {
  const before = acquisitionByRole(bundle, "before");
  const after = acquisitionByRole(bundle, "after");
  const labels = {
    success: { icon: "✓", text: "Validated bundle" },
    degraded: { icon: "!", text: "Validated with warnings" },
    missing: { icon: "!", text: "Required artifact missing" },
    stale: { icon: "!", text: "Validated · stale" },
  } as const;
  return (
    <header className="mission-header">
      <div className="mission-brand">
        <span className="brand-mark" aria-hidden="true">
          EA
        </span>
        <div>
          <p className="overline">EchoAtlas</p>
          <h1>{bundle.mission.title}</h1>
        </div>
      </div>
      <dl className="mission-facts">
        <div>
          <dt>Before</dt>
          <dd>
            <time dateTime={before.acquiredAt}>
              {formatDate(before.acquiredAt)}
            </time>
          </dd>
        </div>
        <div>
          <dt>After</dt>
          <dd>
            <time dateTime={after.acquiredAt}>
              {formatDate(after.acquiredAt)}
            </time>
          </dd>
        </div>
        <div>
          <dt>Review queue</dt>
          <dd>{bundle.candidates.length} candidates</dd>
        </div>
      </dl>
      <div className="mission-status">
        <span className={`status-pill status-${status}`}>
          <span aria-hidden="true">{labels[status].icon}</span>
          {labels[status].text}
        </span>
        <span className="bundle-created">
          Bundle created {formatDate(bundle.createdAt)}
        </span>
      </div>
    </header>
  );
}

function QualityBanner({ bundle, status }: MissionHeaderProps) {
  const warning = bundle.qualityWarnings[0];
  return (
    <section className="quality-banner" aria-labelledby="interpretation-title">
      <span className="warning-mark" aria-hidden="true">
        !
      </span>
      <div>
        <h2 id="interpretation-title">
          {status === "degraded"
            ? "Quality warning"
            : "Interpretation boundary"}
        </h2>
        <p>
          {warning ??
            "Machine-generated candidates require analyst review. The score does not establish cause, damage, intent, or operational status."}
        </p>
      </div>
    </section>
  );
}

interface CandidateQueueProps {
  candidates: CandidateView[];
  currentAssessments: ReadonlyMap<string, AssessmentEvent>;
  selectedCandidateId: string | null;
  onSelect: (candidateId: string) => void;
}

function CandidateQueue({
  candidates,
  currentAssessments,
  selectedCandidateId,
  onSelect,
}: CandidateQueueProps) {
  const [filter, setFilter] = useState<"all" | "pending" | "reviewed">("all");
  const reviewedCount = currentAssessments.size;
  const sortedCandidates = useMemo(
    () =>
      [...candidates]
        .filter((candidate) => {
          if (filter === "all") return true;
          const reviewed = currentAssessments.has(candidate.id);
          return filter === "reviewed" ? reviewed : !reviewed;
        })
        .sort((left, right) => {
          const leftReviewed = currentAssessments.has(left.id) ? 1 : 0;
          const rightReviewed = currentAssessments.has(right.id) ? 1 : 0;
          return (
            leftReviewed - rightReviewed ||
            right.heuristicScore - left.heuristicScore ||
            left.id.localeCompare(right.id)
          );
        }),
    [candidates, currentAssessments, filter],
  );
  return (
    <section
      className="candidate-panel panel"
      id="candidate-queue"
      aria-labelledby="queue-title"
    >
      <div className="panel-heading">
        <div>
          <p className="overline">Review queue</p>
          <h2 id="queue-title">Change candidates</h2>
        </div>
        <span className="count-badge">{candidates.length}</span>
      </div>
      {candidates.length === 0 ? (
        <div className="empty-panel">
          <span aria-hidden="true">◇</span>
          <h3>No change candidates</h3>
          <p>
            The comparison is available, but the declared threshold produced no
            review items.
          </p>
        </div>
      ) : (
        <>
          <div className="queue-filters" aria-label="Candidate status filter">
            {(["all", "pending", "reviewed"] as const).map((option) => (
              <button
                key={option}
                type="button"
                aria-pressed={filter === option}
                onClick={() => setFilter(option)}
              >
                {capitalize(option)}{" "}
                {filterCount(option, candidates.length, reviewedCount)}
              </button>
            ))}
          </div>
          <p className="sort-rule">
            Pending first, then score and candidate ID
          </p>
          {sortedCandidates.length === 0 ? (
            <div className="empty-panel filtered-empty">
              <span aria-hidden="true">◇</span>
              <h3>No {filter} candidates</h3>
              <p>Change the status filter to continue reviewing this bundle.</p>
            </div>
          ) : (
            <ol className="candidate-list" aria-label="Candidates">
              {sortedCandidates.map((candidate, index) => (
                <li key={candidate.id}>
                  <button
                    className="candidate-row"
                    type="button"
                    aria-current={
                      selectedCandidateId === candidate.id ? "true" : undefined
                    }
                    onClick={() => onSelect(candidate.id)}
                  >
                    <span className="candidate-number" aria-hidden="true">
                      {String(index + 1).padStart(2, "0")}
                    </span>
                    <span className="candidate-main">
                      <strong>{candidate.id}</strong>
                      <span>
                        {formatArea(candidate.areaSquareMeters)} ·{" "}
                        {candidate.pixelCount} px
                      </span>
                    </span>
                    <span className="candidate-meta">
                      <span
                        className={`assessment-row-status ${currentAssessments.has(candidate.id) ? "is-reviewed" : "is-pending"}`}
                      >
                        {currentAssessments.has(candidate.id)
                          ? dispositionLabel(
                              currentAssessments.get(candidate.id)!.disposition,
                            )
                          : "Pending"}
                      </span>
                      <span className="candidate-score">
                        {candidate.heuristicScore.toFixed(2)}
                      </span>
                      <span className="candidate-warnings">
                        <span aria-hidden="true">!</span>{" "}
                        {candidate.warningCount}
                      </span>
                    </span>
                  </button>
                </li>
              ))}
            </ol>
          )}
        </>
      )}
    </section>
  );
}

interface TemporalComparisonProps {
  acquisitions: [AcquisitionView, AcquisitionView];
  boundaryLabel: string;
  candidates: CandidateView[];
  comparisonMode: ComparisonMode;
  onComparisonModeChange: (mode: ComparisonMode) => void;
  overlayVisible: boolean;
  onOverlayVisibleChange: (visible: boolean) => void;
  selectedCandidateId: string | null;
  onCandidateSelect: (candidateId: string) => void;
  zoom: number;
  zoomIndex: number;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onReset: () => void;
}

function TemporalComparison({
  acquisitions,
  boundaryLabel,
  candidates,
  comparisonMode,
  onComparisonModeChange,
  overlayVisible,
  onOverlayVisibleChange,
  selectedCandidateId,
  onCandidateSelect,
  zoom,
  zoomIndex,
  onZoomIn,
  onZoomOut,
  onReset,
}: TemporalComparisonProps) {
  const visibleAcquisitions = acquisitions.filter(
    (acquisition) =>
      comparisonMode === "two-up" || acquisition.role === comparisonMode,
  );
  return (
    <section
      className="comparison-panel panel"
      aria-labelledby="comparison-title"
    >
      <div className="panel-heading comparison-heading">
        <div>
          <p className="overline">Temporal comparison</p>
          <h2 id="comparison-title">{boundaryLabel}</h2>
        </div>
        <div className="segmented-control" aria-label="Comparison mode">
          {(["before", "two-up", "after"] as const).map((mode) => (
            <button
              key={mode}
              className={mode === "two-up" ? "mode-two-up" : undefined}
              type="button"
              aria-pressed={comparisonMode === mode}
              onClick={() => onComparisonModeChange(mode)}
            >
              {mode === "two-up" ? "Two-up" : capitalize(mode)}
            </button>
          ))}
        </div>
      </div>
      <div
        className={`comparison-stage comparison-${comparisonMode}`}
        role="region"
        aria-label={`${capitalize(comparisonMode)} synthetic image comparison. ${candidates.length} machine candidates are available.`}
      >
        {visibleAcquisitions.map((acquisition) => (
          <ImageView
            key={acquisition.id}
            acquisition={acquisition}
            candidates={candidates}
            overlayVisible={overlayVisible}
            selectedCandidateId={selectedCandidateId}
            onCandidateSelect={onCandidateSelect}
            zoom={zoom}
          />
        ))}
        <div className="map-tools" aria-label="Synchronized view controls">
          <button
            type="button"
            aria-label="Zoom in both views"
            onClick={onZoomIn}
            disabled={zoomIndex === zoomLevels.length - 1}
          >
            +
          </button>
          <button
            type="button"
            aria-label="Zoom out both views"
            onClick={onZoomOut}
            disabled={zoomIndex === 0}
          >
            −
          </button>
          <button type="button" aria-label="Reset both views" onClick={onReset}>
            ⌂
          </button>
        </div>
        <output className="zoom-status" aria-live="polite">
          View scale {Math.round(zoom * 100)}%
        </output>
      </div>
      <footer className="comparison-footer">
        <div className="legend" aria-label="Map legend">
          <span>
            <i className="legend-aoi" /> Approved boundary
          </span>
          <span>
            <i className="legend-candidate" /> Machine candidate
          </span>
          <span>
            <i className="legend-selected" /> Selected candidate
          </span>
        </div>
        <label className="overlay-toggle">
          <input
            type="checkbox"
            checked={overlayVisible}
            onChange={(event) => onOverlayVisibleChange(event.target.checked)}
          />
          Candidate overlay
        </label>
      </footer>
    </section>
  );
}

interface ImageViewProps {
  acquisition: AcquisitionView;
  candidates: CandidateView[];
  overlayVisible: boolean;
  selectedCandidateId: string | null;
  onCandidateSelect: (candidateId: string) => void;
  zoom: number;
}

function ImageView({
  acquisition,
  candidates,
  overlayVisible,
  selectedCandidateId,
  onCandidateSelect,
  zoom,
}: ImageViewProps) {
  return (
    <figure className={`image-view image-${acquisition.role}`}>
      <figcaption>
        <strong>{acquisition.label}</strong>
        <time dateTime={acquisition.acquiredAt}>
          {formatDate(acquisition.acquiredAt)}
        </time>
      </figcaption>
      {acquisition.artifact.available ? (
        <div
          className="image-transform"
          style={{ transform: `scale(${zoom})` }}
        >
          <img src={acquisition.artifact.src} alt="" />
          <div className="aoi-boundary" aria-hidden="true" />
          {overlayVisible
            ? candidates.map((candidate) => (
                <MapCandidate
                  key={candidate.id}
                  acquisitionLabel={acquisition.label}
                  candidate={candidate}
                  selected={selectedCandidateId === candidate.id}
                  onSelect={onCandidateSelect}
                />
              ))
            : null}
        </div>
      ) : (
        <div className="missing-artifact" role="status">
          <span aria-hidden="true">□</span>
          <strong>{acquisition.label} imagery unavailable</strong>
          <p>The required artifact is missing from this bundle.</p>
        </div>
      )}
    </figure>
  );
}

function MapCandidate({
  acquisitionLabel,
  candidate,
  selected,
  onSelect,
}: {
  acquisitionLabel: string;
  candidate: CandidateView;
  selected: boolean;
  onSelect: (candidateId: string) => void;
}) {
  const position = candidate.mapPosition;
  const style = {
    "--candidate-left": `${position.leftPercent}%`,
    "--candidate-top": `${position.topPercent}%`,
    "--candidate-width": `${position.widthPercent}%`,
    "--candidate-height": `${position.heightPercent}%`,
    "--candidate-rotation": `${position.rotationDegrees}deg`,
  } as CSSProperties;
  return (
    <button
      className="map-candidate"
      type="button"
      style={style}
      aria-label={`Select candidate ${candidate.id} on ${acquisitionLabel} map`}
      aria-pressed={selected}
      onClick={() => onSelect(candidate.id)}
    >
      <span>{candidate.id.slice(-3)}</span>
    </button>
  );
}

function CandidateSummary({
  bundle,
  candidate,
  events,
  currentEvent,
  assessmentUnavailableReason,
  onStartAssessment,
}: {
  bundle: WorkbenchBundle;
  candidate: CandidateView | null;
  events: AssessmentEvent[];
  currentEvent: AssessmentEvent | null;
  assessmentUnavailableReason: string | null;
  onStartAssessment: (candidateId: string, invoker: HTMLElement) => void;
}) {
  const [tab, setTab] = useState<
    "review" | "provenance" | "processing" | "history"
  >("review");
  const evidenceExport = useMemo(
    () =>
      candidate
        ? createCandidateEvidenceExport({
            bundle,
            candidate,
            assessments: events,
            exportedAt: new Date().toISOString(),
          })
        : null,
    [bundle, candidate, events],
  );
  return (
    <aside className="summary-panel panel" aria-labelledby="summary-title">
      <div className="panel-heading">
        <div>
          <p className="overline">Evidence summary</p>
          <h2 id="summary-title">{candidate?.id ?? "No candidate selected"}</h2>
        </div>
        {candidate ? (
          <span
            className={`status-pill ${currentEvent ? `status-${currentEvent.disposition}` : "status-candidate"}`}
          >
            {currentEvent
              ? dispositionLabel(currentEvent.disposition)
              : "Pending"}
          </span>
        ) : null}
      </div>
      {candidate ? (
        <div className="summary-content">
          <div className="evidence-tabs" role="tablist" aria-label="Evidence">
            {evidenceTabs.map((option) => (
              <button
                key={option}
                type="button"
                role="tab"
                aria-selected={tab === option}
                aria-controls={`evidence-${option}`}
                tabIndex={tab === option ? 0 : -1}
                onClick={() => setTab(option)}
                onKeyDown={(event) => moveEvidenceTab(event, option, setTab)}
              >
                {capitalize(option)}
              </button>
            ))}
          </div>
          {tab === "review" ? <ReviewEvidence candidate={candidate} /> : null}
          {tab === "provenance" ? (
            <ProvenanceEvidence bundle={bundle} candidate={candidate} />
          ) : null}
          {tab === "processing" ? (
            <ProcessingEvidence bundle={bundle} candidate={candidate} />
          ) : null}
          {tab === "history" ? (
            <section id="evidence-history" role="tabpanel" aria-label="History">
              {events.length > 0 ? (
                <AssessmentHistory
                  events={events}
                  currentEvent={currentEvent}
                />
              ) : (
                <p className="evidence-empty">No assessment events recorded.</p>
              )}
            </section>
          ) : null}
          {evidenceExport ? (
            <a
              className="secondary-button evidence-export"
              href={createEvidenceDownloadHref(evidenceExport)}
              download={`${bundle.bundleId}-${candidate.id}-evidence.json`}
            >
              Export evidence JSON
            </a>
          ) : null}
          {assessmentUnavailableReason ? (
            <div className="read-only-notice" role="note">
              <strong>Read-only inspection</strong>
              <p>{assessmentUnavailableReason}</p>
            </div>
          ) : (
            <>
              <button
                className="primary-button"
                type="button"
                onClick={(event) =>
                  onStartAssessment(candidate.id, event.currentTarget)
                }
              >
                {currentEvent ? "Correct assessment" : "Record assessment"}
              </button>
              <p className="future-boundary">
                Every save appends an immutable audit event.
              </p>
            </>
          )}
        </div>
      ) : (
        <div className="empty-panel summary-empty">
          <span aria-hidden="true">◇</span>
          <h3>Select a candidate</h3>
          <p>
            Use the review queue or either map to inspect its measurements and
            limitations.
          </p>
        </div>
      )}
    </aside>
  );
}

function ReviewEvidence({ candidate }: { candidate: CandidateView }) {
  return (
    <section id="evidence-review" role="tabpanel" aria-label="Review">
      <div className="score-card">
        <span>Heuristic change score</span>
        <strong>{candidate.heuristicScore.toFixed(2)}</strong>
        <p>
          Ranking signal from deterministic fixture measurements. It is not
          calibrated confidence, a probability, or a confirmed finding.
        </p>
      </div>
      <dl className="summary-metrics">
        <div>
          <dt>Area</dt>
          <dd>{formatArea(candidate.areaSquareMeters)}</dd>
        </div>
        <div>
          <dt>Pixels</dt>
          <dd>{candidate.pixelCount}</dd>
        </div>
        <div>
          <dt>Warnings</dt>
          <dd>{candidate.warningCount}</dd>
        </div>
      </dl>
      <EvidenceWarnings warnings={candidate.warnings} />
    </section>
  );
}

function ProvenanceEvidence({
  bundle,
  candidate,
}: {
  bundle: WorkbenchBundle;
  candidate: CandidateView;
}) {
  const artifacts = bundle.evidence.artifacts;
  return (
    <section
      className="evidence-section"
      id="evidence-provenance"
      role="tabpanel"
      aria-label="Provenance"
    >
      <div className="lineage-notice">
        <strong>Synthetic lineage</strong>
        <p>{bundle.evidence.lineageNotice}</p>
      </div>
      <h3>Acquisition comparison</h3>
      <div className="acquisition-evidence">
        {bundle.evidence.acquisitions.map((acquisition) => (
          <article key={acquisition.acquisitionId}>
            <strong>{acquisition.provider}</strong>
            <span>
              {acquisition.productType} · {acquisition.polarization}
            </span>
            <span>
              {acquisition.resolutionMeters} m · incidence{" "}
              {acquisition.incidenceAngleDegrees}°
            </span>
            <EvidenceSourceLink link={acquisition.source} />
            <Checksum
              algorithm={acquisition.checksum.algorithm}
              value={acquisition.checksum.value}
            />
          </article>
        ))}
      </div>
      <h3>Referenced artifacts</h3>
      <ul className="artifact-list">
        {artifacts.map((artifact) => (
          <li key={artifact.id}>
            <div>
              <strong>{artifact.label}</strong>
              <span>
                {candidate.evidenceArtifactIds.includes(artifact.id)
                  ? "Candidate evidence"
                  : "Run artifact"}
                {" · "}
                {artifact.mediaType}
                {artifact.available
                  ? ` · ${formatBytes(artifact.sizeBytes)}`
                  : " · unavailable"}
              </span>
            </div>
            {artifact.available ? (
              <a href={artifact.path} target="_blank" rel="noreferrer">
                Open artifact
              </a>
            ) : (
              <span className="unavailable-link">Unavailable</span>
            )}
            <Checksum algorithm="SHA-256" value={artifact.sha256} />
          </li>
        ))}
      </ul>
      <p className="attribution-line">{bundle.evidence.attribution}</p>
      <EvidenceSourceLink link={bundle.evidence.license} />
    </section>
  );
}

function ProcessingEvidence({
  bundle,
  candidate,
}: {
  bundle: WorkbenchBundle;
  candidate: CandidateView;
}) {
  const unavailable = bundle.evidence.artifacts.filter(
    (artifact) => !artifact.available,
  );
  return (
    <section
      className="evidence-section"
      id="evidence-processing"
      role="tabpanel"
      aria-label="Processing"
    >
      <dl className="processing-facts">
        <div>
          <dt>Run</dt>
          <dd>{bundle.evidence.run.id}</dd>
        </div>
        <div>
          <dt>Software</dt>
          <dd>{bundle.evidence.software.version}</dd>
        </div>
        <div>
          <dt>Commit</dt>
          <dd>{bundle.evidence.software.commit}</dd>
        </div>
      </dl>
      <h3>Run parameters</h3>
      <dl className="parameter-list">
        {bundle.evidence.run.parameters.map((parameter) => (
          <div key={parameter.name}>
            <dt>{parameter.name}</dt>
            <dd>{parameter.value}</dd>
          </div>
        ))}
      </dl>
      <EvidenceWarnings
        warnings={[
          ...candidate.warnings,
          ...bundle.evidence.warnings,
          ...unavailable.map(
            (artifact) =>
              `${artifact.label} is unavailable; valid evidence remains usable.`,
          ),
        ]}
      />
    </section>
  );
}

function EvidenceWarnings({ warnings }: { warnings: string[] }) {
  return (
    <div className="summary-warning">
      <span aria-hidden="true">!</span>
      <div>
        <strong>Limitations and warnings</strong>
        <ul>
          {warnings.map((warning) => (
            <li key={warning}>{warning}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}

function EvidenceSourceLink({
  link,
}: {
  link: WorkbenchBundle["evidence"]["license"];
}) {
  if (link.status === "unavailable" || !link.href) {
    return (
      <span className="unavailable-link">
        {link.label} · source link unavailable
      </span>
    );
  }
  return (
    <a href={link.href} target="_blank" rel="noreferrer">
      {link.label}
    </a>
  );
}

function Checksum({ algorithm, value }: { algorithm: string; value: string }) {
  return (
    <span className="checksum" title={`${algorithm}: ${value}`}>
      <span className="sr-status">
        {algorithm}: {value}
      </span>
      <span aria-hidden="true">
        {algorithm} · {value.slice(0, 12)}…
      </span>
    </span>
  );
}

function AssessmentHistory({
  events,
  currentEvent,
}: {
  events: AssessmentEvent[];
  currentEvent: AssessmentEvent | null;
}) {
  return (
    <section className="assessment-history" aria-labelledby="history-title">
      <div className="history-heading">
        <h3 id="history-title">Assessment history</h3>
        <span>
          {events.length} {events.length === 1 ? "event" : "events"}
        </span>
      </div>
      <ol>
        {[...events].reverse().map((event) => {
          const current = event.eventId === currentEvent?.eventId;
          return (
            <li key={event.eventId}>
              <div>
                <strong>{dispositionLabel(event.disposition)}</strong>
                <span>{current ? "Current" : "Superseded"}</span>
              </div>
              <p>{event.note || "No analyst note."}</p>
              <small>
                {event.eventId} · {formatTimestamp(event.createdAt)}
              </small>
            </li>
          );
        })}
      </ol>
    </section>
  );
}

export function StateNotice({
  kind,
  title,
  message,
  action,
  onAction,
}: {
  kind: "loading" | "warning" | "error" | "empty";
  title: string;
  message: string;
  action?: string;
  onAction?: () => void;
}) {
  const titleId = useId();
  return (
    <section
      className={`state-notice state-${kind}`}
      role={kind === "error" ? "alert" : "status"}
      aria-labelledby={titleId}
    >
      <span className="state-icon" aria-hidden="true">
        {kind === "error" ? "×" : kind === "loading" ? "…" : "!"}
      </span>
      <div>
        <h2 id={titleId}>{title}</h2>
        <p>{message}</p>
      </div>
      {action && onAction ? (
        <button className="secondary-button" type="button" onClick={onAction}>
          {action}
        </button>
      ) : null}
    </section>
  );
}

function acquisitionByRole(bundle: WorkbenchBundle, role: "before" | "after") {
  const acquisition = bundle.acquisitions.find((item) => item.role === role);
  if (!acquisition)
    throw new Error(`validated bundle is missing ${role} acquisition`);
  return acquisition;
}

function formatDate(timestamp: string) {
  const date = new Date(timestamp);
  const month = date.toLocaleString("en-US", {
    month: "short",
    timeZone: "UTC",
  });
  return `${String(date.getUTCDate()).padStart(2, "0")} ${month} ${date.getUTCFullYear()}`;
}

function formatArea(area: number) {
  return `${new Intl.NumberFormat("en-US").format(area)} m²`;
}

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  return `${(bytes / 1024).toFixed(1)} KB`;
}

function capitalize(value: string) {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function filterCount(
  filter: "all" | "pending" | "reviewed",
  total: number,
  reviewed: number,
) {
  if (filter === "pending") return `(${total - reviewed})`;
  if (filter === "reviewed") return `(${reviewed})`;
  return `(${total})`;
}

function currentAssessmentMap(events: AssessmentEvent[]) {
  const current = new Map<string, AssessmentEvent>();
  for (const event of events) current.set(event.candidateId, event);
  return current;
}

function createAssessmentRequestId() {
  assessmentRequestSequence += 1;
  return `assessment-request-${assessmentRequestSequence}`;
}

function formatTimestamp(timestamp: string) {
  return new Date(timestamp).toLocaleString("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "UTC",
  });
}

function getInitialMode(): ComparisonMode {
  if (
    typeof window.matchMedia === "function" &&
    window.matchMedia("(max-width: 767px)").matches
  ) {
    return "before";
  }
  return "two-up";
}

const evidenceTabs = ["review", "provenance", "processing", "history"] as const;
type EvidenceTab = (typeof evidenceTabs)[number];

function moveEvidenceTab(
  event: KeyboardEvent<HTMLButtonElement>,
  current: EvidenceTab,
  setTab: (tab: EvidenceTab) => void,
) {
  const currentIndex = evidenceTabs.indexOf(current);
  const nextIndex =
    event.key === "ArrowRight" || event.key === "ArrowDown"
      ? (currentIndex + 1) % evidenceTabs.length
      : event.key === "ArrowLeft" || event.key === "ArrowUp"
        ? (currentIndex - 1 + evidenceTabs.length) % evidenceTabs.length
        : event.key === "Home"
          ? 0
          : event.key === "End"
            ? evidenceTabs.length - 1
            : null;
  if (nextIndex === null) return;
  event.preventDefault();
  const next = evidenceTabs[nextIndex];
  setTab(next);
  const tabs =
    event.currentTarget.parentElement?.querySelectorAll<HTMLElement>(
      '[role="tab"]',
    );
  tabs?.[nextIndex]?.focus();
}

function useMediaQuery(query: string) {
  const [matches, setMatches] = useState(() =>
    typeof window.matchMedia === "function"
      ? window.matchMedia(query).matches
      : false,
  );
  useEffect(() => {
    if (typeof window.matchMedia !== "function") return;
    const media = window.matchMedia(query);
    const synchronize = (event: MediaQueryListEvent | MediaQueryList) =>
      setMatches(event.matches);
    media.addEventListener("change", synchronize);
    synchronize(media);
    return () => media.removeEventListener("change", synchronize);
  }, [query]);
  return matches;
}
