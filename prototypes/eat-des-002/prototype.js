const body = document.body;
const stateSelect = document.querySelector("#review-state");
const notice = document.querySelector("#state-notice");
const title = document.querySelector("#state-title");
const kicker = document.querySelector("#state-kicker");
const message = document.querySelector("#state-message");
const action = document.querySelector("#state-action");
const list = document.querySelector("#result-list");
const empty = document.querySelector("#empty-results");
const count = document.querySelector("#result-count");
const summary = document.querySelector("#result-summary");
const beforeValue = document.querySelector("#before-value");
const afterValue = document.querySelector("#after-value");
const reviewPair = document.querySelector("#review-pair");
const warning = document.querySelector("#pair-warning");
const navCount = document.querySelector("#nav-count");
const dialog = document.querySelector("#handoff-dialog");
const announcement = document.querySelector("#announcement");
let before = null;
let after = null;
const states = {
  ready: null,
  loading: {
    k: "Catalog query",
    t: "Searching bounded provider metadata",
    m: "Checking Umbra and Sentinel-1 for the declared AOI and date range. No raster imagery is downloading.",
    a: "Cancel search",
  },
  empty: {
    k: "Completed search",
    t: "No provider reported coverage for this query",
    m: "The globe remains navigable. This result does not mean the location has never been imaged.",
    a: "Edit search",
  },
  partial: {
    k: "Partial result",
    t: "Sentinel-1 completed; Umbra reached its bounded sample limit",
    m: "15 Sentinel-1 records remain available. Umbra coverage may be incomplete and is not presented as exhaustive.",
    a: "Refine Umbra query",
  },
  stale: {
    k: "Cached result",
    t: "These results are older than the freshness policy",
    m: "Captured 18 minutes ago. Review is available, but run a fresh search before creating a processing manifest.",
    a: "Refresh search",
  },
  rate: {
    k: "Provider unavailable",
    t: "Umbra is temporarily rate limited",
    m: "Sentinel-1 results remain available. No missing Umbra footprint is inferred to mean no coverage.",
    a: "Retry Umbra",
  },
  invalid: {
    k: "Search not run",
    t: "The AOI exceeds the supported 25-square-degree limit",
    m: "Edit the boundary or enter a smaller coordinate extent. No provider was contacted.",
    a: "Edit AOI",
  },
  offline: {
    k: "Network unavailable",
    t: "Catalog search is offline",
    m: "The basemap may remain visible from cache, but it is not evidence of current provider coverage.",
    a: "Retry connection",
  },
  permission: {
    k: "Capability boundary",
    t: "This workspace cannot access the selected provider",
    m: "Available public results remain visible. Restricted provider names, items, and counts are not exposed.",
    a: "Review access",
  },
};
function setState(name) {
  body.dataset.reviewState = name;
  const s = states[name];
  notice.hidden = !s;
  list.hidden = name === "empty";
  empty.hidden = name !== "empty";
  count.textContent =
    name === "empty"
      ? "0"
      : name === "partial" || name === "rate" || name === "permission"
        ? "2"
        : "4";
  summary.textContent =
    name === "empty"
      ? "Completed · 0 results"
      : name === "partial"
        ? "2 Sentinel-1 · Umbra partial"
        : name === "rate"
          ? "2 Sentinel-1 · Umbra unavailable"
          : "2 Sentinel-1 · 2 Umbra";
  if (!s) return;
  kicker.textContent = s.k;
  title.textContent = s.t;
  message.textContent = s.m;
  action.textContent = s.a;
  announce(s.t);
}
function select(slot, id, card) {
  if (slot === "before") before = id;
  else after = id;
  document.querySelectorAll(".result-card").forEach((c) => {
    c.dataset.before = String(c.dataset.id === before);
    c.dataset.after = String(c.dataset.id === after);
  });
  beforeValue.textContent = before || "Not selected";
  afterValue.textContent = after || "Not selected";
  const ready = Boolean(before && after && before !== after);
  reviewPair.disabled = !ready;
  warning.textContent = ready
    ? "Two acquisitions selected. Review comparability before processing."
    : "Select two acquisitions. Availability does not establish scientific comparability.";
  navCount.textContent = ready ? "· pair retained" : "· no pair";
  announce(
    `${id} selected as ${slot}. ${ready ? "Candidate pair ready for review." : ""}`,
  );
}
function announce(text) {
  announcement.textContent = "";
  requestAnimationFrame(() => (announcement.textContent = text));
}
document.querySelectorAll(".result-card").forEach((card) => {
  card.querySelectorAll("[data-zoom], [data-slot]").forEach((button) => {
    button.setAttribute(
      "aria-label",
      `${button.textContent.trim()} ${card.dataset.id}`,
    );
  });
});
stateSelect.addEventListener("change", () => setState(stateSelect.value));
document.querySelector(".place-search").addEventListener("submit", (e) => {
  e.preventDefault();
  setState("loading");
  stateSelect.value = "loading";
});
document.querySelector("#search-button").addEventListener("click", () => {
  stateSelect.value = "loading";
  setState("loading");
});
document
  .querySelectorAll("[data-slot]")
  .forEach((button) =>
    button.addEventListener("click", () =>
      select(
        button.dataset.slot,
        button.closest(".result-card").dataset.id,
        button.closest(".result-card"),
      ),
    ),
  );
document
  .querySelectorAll("[data-zoom]")
  .forEach((button) =>
    button.addEventListener("click", () =>
      announce(
        `${button.dataset.zoom} footprint centered on the map. Keyboard focus remains in the results list.`,
      ),
    ),
  );
document.querySelector("#edit-aoi").addEventListener("click", () => {
  document.querySelector("#draw-help").hidden = false;
  announce(
    "AOI edit mode. Exact coordinate fields remain available in the filter panel.",
  );
});
document.querySelector("#done-aoi").addEventListener("click", () => {
  document.querySelector("#draw-help").hidden = true;
  announce("AOI edit complete. Search results are now stale until rerun.");
});
reviewPair.addEventListener("click", () => {
  document.querySelector("#dialog-before").textContent = before;
  document.querySelector("#dialog-after").textContent = after;
  dialog.showModal();
  document.querySelector("#handoff-title").focus();
});
document.querySelector("#analyze-nav").addEventListener("click", () => {
  if (reviewPair.disabled)
    announce("Choose a before and after acquisition before entering Analyze.");
  else reviewPair.click();
});
setState("ready");
