const body = document.body;
const reviewState = document.querySelector("#review-state");
const stateNotice = document.querySelector("#state-notice");
const stateKicker = document.querySelector("#state-kicker");
const stateTitle = document.querySelector("#state-title");
const stateMessage = document.querySelector("#state-message");
const stateAction = document.querySelector("#state-action");
const bundleStatus = document.querySelector("#bundle-status");
const bundleStatusIcon = bundleStatus.querySelector(".status-icon");
const freshness = document.querySelector("#freshness");
const qualityBanner = document.querySelector("#quality-banner");
const qualityTitle = document.querySelector("#quality-title");
const qualityCopy = document.querySelector("#quality-copy");
const candidateRows = [...document.querySelectorAll("[data-candidate]")];
const evidenceTitle = document.querySelector("#evidence-title");
const candidateStatus = document.querySelector("#candidate-status");
const orientationPanel = document.querySelector("#orientation-panel");
const evidenceContent = document.querySelector("#evidence-content");
const disabledAssessment = document.querySelector("#disabled-assessment");
const recordAssessment = document.querySelector("#record-assessment");
const recordCorrection = document.querySelector("#record-correction");
const assessmentDialog = document.querySelector("#assessment-dialog");
const assessmentTitle = document.querySelector("#assessment-title");
const assessmentForm = document.querySelector("#assessment-form");
const saveAssessment = document.querySelector("#save-assessment");
const assessmentError = document.querySelector("#assessment-error");
const emptyHistory = document.querySelector("#empty-history");
const historyEvent = document.querySelector("#history-event");
const statusAnnouncement = document.querySelector("#status-announcement");
const reviewProgress = document.querySelector("#review-progress");
const queueProgress = document.querySelector("#queue-progress-value");
const progressTrack = document.querySelector(".progress-track span");
const overlayToggle = document.querySelector("#overlay-toggle");

const states = {
  default: null,
  selected: null,
  assessed: null,
  loading: {
    kicker: "Bundle validation",
    title: "Validating bundle",
    message:
      "Checking contract version, file integrity, safe paths, and references.",
    action: "Cancel",
    status: "Validating bundle",
    icon: "…",
    statusClass: "status-system",
  },
  empty: {
    kicker: "Validated bundle",
    title: "No change candidates",
    message:
      "The comparison is available, but the declared threshold produced no review candidates.",
    action: "Inspect run parameters",
    status: "Validated · 0 candidates",
    icon: "✓",
    statusClass: "status-system",
  },
  invalid: {
    kicker: "Bundle rejected",
    title: "This bundle cannot be opened safely",
    message:
      "Manifest validation failed at artifact path. No bundle artifacts were rendered. Diagnostic EA-BND-104.",
    action: "Choose another bundle",
    status: "Bundle rejected",
    icon: "×",
    statusClass: "status-error",
  },
  degraded: {
    kicker: "Validated with warnings",
    title: "One optional artifact is unavailable",
    message:
      "Core before/after evidence remains usable. The candidate overlay is unavailable and clearly marked.",
    action: "Inspect missing evidence",
    status: "Validated with warnings",
    icon: "!",
    statusClass: "status-warning",
  },
  partial: {
    kicker: "Partial output",
    title: "Core comparison completed; overlay failed",
    message:
      "Completed outputs remain intact. Retry only the optional candidate overlay.",
    action: "Retry failed output",
    status: "Partial output",
    icon: "!",
    statusClass: "status-warning",
  },
  stale: {
    kicker: "Freshness warning",
    title: "Bundle is older than the review policy",
    message:
      "Captured 10 February 2025. Loaded today. Review is available, but freshness must remain visible.",
    action: "Continue with stale data",
    status: "Validated · stale",
    icon: "!",
    statusClass: "status-warning",
  },
  permission: {
    kicker: "Remote capability unavailable",
    title: "This local prototype has no remote workspace",
    message:
      "Remote names and metadata are not revealed. Return to the validated local bundle.",
    action: "Return to local bundle",
    status: "Remote capability unavailable",
    icon: "—",
    statusClass: "status-neutral",
  },
};

function setReviewState(state) {
  body.dataset.reviewState = state;
  resetStateCopy();
  if (state === "selected") selectCandidate("C-001");
  if (state === "assessed") {
    selectCandidate("C-001");
    setAssessed(true);
    showTab("history");
  }
  const configuration = states[state];
  stateNotice.hidden = !configuration;
  if (!configuration) return;
  stateKicker.textContent = configuration.kicker;
  stateTitle.textContent = configuration.title;
  stateMessage.textContent = configuration.message;
  stateAction.textContent = configuration.action;
  bundleStatus.className = `status-pill ${configuration.statusClass}`;
  bundleStatusIcon.textContent = configuration.icon;
  bundleStatus.lastChild.textContent = ` ${configuration.status}`;
  if (state === "stale") {
    freshness.textContent = "Captured 18 months ago";
    qualityTitle.textContent = "Stale review material";
    qualityCopy.textContent =
      "Freshness is outside the review policy. Continuing does not refresh source evidence.";
  }
  if (state === "degraded" || state === "partial") {
    qualityTitle.textContent =
      state === "partial" ? "Optional output failed" : "Evidence is degraded";
    qualityCopy.textContent =
      "The missing candidate overlay is explicitly unavailable; core evidence remains valid.";
  }
  if (state === "invalid" || state === "permission")
    qualityBanner.hidden = true;
}

function resetStateCopy() {
  deselectCandidates();
  setAssessed(false);
  stateNotice.hidden = true;
  qualityBanner.hidden = false;
  bundleStatus.className = "status-pill status-system";
  bundleStatusIcon.textContent = "✓";
  bundleStatus.lastChild.textContent = " Validated bundle";
  freshness.textContent = "Loaded 4 minutes ago";
  qualityTitle.textContent = "Interpretation boundary";
  qualityCopy.textContent =
    "Machine-generated candidates require analyst review. The score does not establish cause, damage, intent, or operational status.";
}

function selectCandidate(candidateId) {
  body.dataset.selectedCandidate = candidateId;
  candidateRows.forEach((row) => {
    const selected = row.dataset.candidate === candidateId;
    if (selected) row.setAttribute("aria-current", "true");
    else row.removeAttribute("aria-current");
  });
  evidenceTitle.textContent = candidateId;
  candidateStatus.hidden = false;
  orientationPanel.hidden = true;
  evidenceContent.hidden = false;
  disabledAssessment.hidden = true;
  showTab("review");
  announce(`Candidate ${candidateId} selected. Evidence inspector updated.`);
}

function deselectCandidates() {
  delete body.dataset.selectedCandidate;
  candidateRows.forEach((row) => row.removeAttribute("aria-current"));
  evidenceTitle.textContent = "No candidate selected";
  candidateStatus.hidden = true;
  orientationPanel.hidden = false;
  evidenceContent.hidden = true;
  disabledAssessment.hidden = false;
}

function showTab(tabName) {
  document.querySelectorAll("[role='tab']").forEach((tab) => {
    tab.setAttribute("aria-selected", String(tab.dataset.tab === tabName));
  });
  document.querySelectorAll("[role='tabpanel']").forEach((panel) => {
    panel.hidden = panel.id !== `panel-${tabName}`;
  });
}

function setAssessed(assessed) {
  emptyHistory.hidden = assessed;
  historyEvent.hidden = !assessed;
  recordAssessment.hidden = assessed;
  recordCorrection.hidden = !assessed;
  candidateStatus.textContent = assessed ? "Needs context" : "Pending";
  candidateStatus.className = assessed
    ? "status-pill status-context"
    : "status-pill status-candidate";
  reviewProgress.textContent = assessed ? "1 of 3 reviewed" : "0 of 3 reviewed";
  queueProgress.textContent = assessed ? "1 / 3" : "0 / 3";
  progressTrack.style.width = assessed ? "33.333%" : "0";
}

function openAssessment() {
  assessmentForm.reset();
  saveAssessment.disabled = true;
  assessmentError.hidden = true;
  assessmentDialog.showModal();
  assessmentTitle.focus();
}

function setComparisonMode(mode, announceChange = true) {
  body.dataset.comparisonMode = mode;
  document.querySelectorAll("[data-mode]").forEach((modeButton) => {
    modeButton.setAttribute(
      "aria-pressed",
      String(modeButton.dataset.mode === mode),
    );
  });
  if (announceChange) {
    const label = document.querySelector(`[data-mode="${mode}"]`).textContent;
    announce(`${label} comparison view active.`);
  }
}

function announce(message) {
  statusAnnouncement.textContent = message;
  statusAnnouncement.classList.add("visible");
  window.clearTimeout(announce.timeout);
  announce.timeout = window.setTimeout(
    () => statusAnnouncement.classList.remove("visible"),
    3600,
  );
}

reviewState.addEventListener("change", () => setReviewState(reviewState.value));

candidateRows.forEach((row) => {
  row.addEventListener("click", () => selectCandidate(row.dataset.candidate));
});

document.querySelectorAll("[data-mode]").forEach((button) => {
  button.addEventListener("click", () => {
    setComparisonMode(button.dataset.mode);
  });
});

document.querySelectorAll("[data-tab]").forEach((tab) => {
  tab.addEventListener("click", () => showTab(tab.dataset.tab));
});

document.querySelectorAll("[data-open-evidence]").forEach((button) => {
  button.addEventListener("click", () => {
    if (!body.dataset.selectedCandidate) selectCandidate("C-001");
    showTab(button.dataset.openEvidence);
    document.querySelector("#evidence").scrollIntoView({ block: "nearest" });
  });
});

recordAssessment.addEventListener("click", openAssessment);
recordCorrection.addEventListener("click", openAssessment);

assessmentForm.addEventListener("change", () => {
  saveAssessment.disabled = !assessmentForm.elements.decision.value;
});

assessmentForm.addEventListener("submit", (event) => {
  if (event.submitter?.value !== "default") return;
  event.preventDefault();
  assessmentDialog.close();
  setAssessed(true);
  showTab("history");
  reviewState.value = "assessed";
  body.dataset.reviewState = "assessed";
  announce("Assessment saved. Candidate C-001 marked needs context.");
});

overlayToggle.addEventListener("change", () => {
  body.dataset.overlay = overlayToggle.checked ? "visible" : "hidden";
  announce(`Candidate overlay ${overlayToggle.checked ? "shown" : "hidden"}.`);
});

stateAction.addEventListener("click", () => {
  if (body.dataset.reviewState === "stale") {
    announce("Continuing with stale data. Freshness warning remains visible.");
    return;
  }
  reviewState.value = "default";
  setReviewState("default");
  announce("Returned to the default validated bundle state.");
});

const compactComparison = window.matchMedia("(max-width: 767px)");
function synchronizeCompactComparison(event) {
  if (event.matches && body.dataset.comparisonMode === "two-up")
    setComparisonMode("before", false);
  if (!event.matches && body.dataset.comparisonMode !== "two-up")
    setComparisonMode("two-up", false);
}
compactComparison.addEventListener("change", synchronizeCompactComparison);
synchronizeCompactComparison(compactComparison);
setReviewState("default");
