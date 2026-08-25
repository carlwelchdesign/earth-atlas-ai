import { useEffect, useId, useMemo, useState, type CSSProperties } from "react";

import type {
  AcquisitionView,
  CandidateView,
  ComparisonMode,
  WorkbenchBundle,
} from "./model";

interface WorkbenchProps {
  bundle: WorkbenchBundle;
}

const zoomLevels = [1, 1.2, 1.4] as const;

export function Workbench({ bundle }: WorkbenchProps) {
  const [selectedCandidateId, setSelectedCandidateId] = useState<string | null>(
    null,
  );
  const [comparisonMode, setComparisonMode] =
    useState<ComparisonMode>(getInitialMode);
  const [overlayVisible, setOverlayVisible] = useState(true);
  const [zoomIndex, setZoomIndex] = useState(0);
  const selectedCandidate =
    bundle.candidates.find(
      (candidate) => candidate.id === selectedCandidateId,
    ) ?? null;
  const missingAcquisitions = bundle.acquisitions.filter(
    (acquisition) => !acquisition.artifact.available,
  );
  const degraded =
    bundle.status === "partial" || bundle.qualityWarnings.length > 0;
  const status =
    missingAcquisitions.length > 0
      ? "missing"
      : degraded
        ? "degraded"
        : "success";
  const zoom = zoomLevels[zoomIndex];

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
      {status === "missing" ? (
        <StateNotice
          kind="warning"
          title="Required comparison artifact is missing"
          message={`${missingAcquisitions.map((item) => item.label).join(" and ")} imagery is unavailable. Available evidence remains visible, but the comparison is incomplete.`}
          action="Choose another bundle"
        />
      ) : null}
      {degraded ? (
        <StateNotice
          kind="warning"
          title="Validated bundle with quality warnings"
          message={
            bundle.qualityWarnings[0] ?? "An optional output is unavailable."
          }
          action="Inspect warning"
        />
      ) : null}
      <main className="workbench-grid">
        <CandidateQueue
          candidates={bundle.candidates}
          selectedCandidateId={selectedCandidateId}
          onSelect={setSelectedCandidateId}
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
          onCandidateSelect={setSelectedCandidateId}
          zoom={zoom}
          zoomIndex={zoomIndex}
          onZoomIn={() =>
            setZoomIndex((index) => Math.min(index + 1, zoomLevels.length - 1))
          }
          onZoomOut={() => setZoomIndex((index) => Math.max(index - 1, 0))}
          onReset={() => setZoomIndex(0)}
        />
        <CandidateSummary candidate={selectedCandidate} />
      </main>
      <footer className="workbench-footer">
        <span>Synthetic fixture · no satellite measurement represented</span>
        <span>Bundle contract {bundle.contractVersion}</span>
      </footer>
      <div className="sr-status" role="status" aria-live="polite">
        {selectionAnnouncement}
      </div>
    </div>
  );
}

interface MissionHeaderProps {
  bundle: WorkbenchBundle;
  status: "success" | "degraded" | "missing";
}

function MissionHeader({ bundle, status }: MissionHeaderProps) {
  const before = acquisitionByRole(bundle, "before");
  const after = acquisitionByRole(bundle, "after");
  const labels = {
    success: { icon: "✓", text: "Validated bundle" },
    degraded: { icon: "!", text: "Validated with warnings" },
    missing: { icon: "!", text: "Required artifact missing" },
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
  selectedCandidateId: string | null;
  onSelect: (candidateId: string) => void;
}

function CandidateQueue({
  candidates,
  selectedCandidateId,
  onSelect,
}: CandidateQueueProps) {
  const sortedCandidates = useMemo(
    () =>
      [...candidates].sort(
        (left, right) =>
          right.heuristicScore - left.heuristicScore ||
          left.id.localeCompare(right.id),
      ),
    [candidates],
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
          <p className="sort-rule">Highest score, then candidate ID</p>
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
                    <span className="candidate-score">
                      {candidate.heuristicScore.toFixed(2)}
                    </span>
                    <span className="candidate-warnings">
                      <span aria-hidden="true">!</span> {candidate.warningCount}
                    </span>
                  </span>
                </button>
              </li>
            ))}
          </ol>
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

function CandidateSummary({ candidate }: { candidate: CandidateView | null }) {
  return (
    <aside className="summary-panel panel" aria-labelledby="summary-title">
      <div className="panel-heading">
        <div>
          <p className="overline">Evidence summary</p>
          <h2 id="summary-title">{candidate?.id ?? "No candidate selected"}</h2>
        </div>
        {candidate ? (
          <span className="status-pill status-candidate">Pending</span>
        ) : null}
      </div>
      {candidate ? (
        <div className="summary-content">
          <div className="score-card">
            <span>Heuristic change score</span>
            <strong>{candidate.heuristicScore.toFixed(2)}</strong>
            <p>Ranking signal only—not calibrated confidence or a finding.</p>
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
          <div className="summary-warning">
            <span aria-hidden="true">!</span>
            <p>
              Registration, moisture, slope, layover, and shadow can create
              apparent differences.
            </p>
          </div>
          <button className="primary-button" type="button" disabled>
            Record assessment
          </button>
          <p className="future-boundary">
            Assessment actions begin in EAT-009.
          </p>
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
      {action ? (
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

function capitalize(value: string) {
  return value.charAt(0).toUpperCase() + value.slice(1);
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
