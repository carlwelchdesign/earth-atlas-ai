import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { KeyboardEvent, RefObject } from "react";

import {
  CatalogClientError,
  HttpPlaceSearchAdapter,
  HttpCatalogSearchClient,
  type CatalogSearchClient,
  type PlaceSearchAdapter,
} from "./catalog";
import { defaultBasemap, type BasemapConfig } from "./basemap";
import { MapSurface } from "./MapSurface";
import {
  BINGHAM_CANYON_BBOX,
  formatProvider,
  itemKey,
  polygonFromBbox,
  validateBbox,
  type BBox,
  type CatalogItem,
  type CatalogSearchResponse,
  type CatalogWarning,
  type ProviderId,
  type ProviderReport,
} from "./model";

type Pair = { before: CatalogItem | null; after: CatalogItem | null };

export function Explore({
  onAnalyze,
  catalog = new HttpCatalogSearchClient(),
  places = new HttpPlaceSearchAdapter(),
  basemap = defaultBasemap(),
  renderMap = true,
}: {
  onAnalyze: () => void;
  catalog?: CatalogSearchClient;
  places?: PlaceSearchAdapter;
  basemap?: BasemapConfig;
  renderMap?: boolean;
}) {
  const [query, setQuery] = useState("Bingham Canyon, Utah");
  const [placeLabel, setPlaceLabel] = useState("Bingham Canyon, Utah");
  const [placeSource, setPlaceSource] = useState<{
    provider: string;
    attributionUrl: string | null;
  }>({ provider: "Preset AOI", attributionUrl: null });
  const [placeLoading, setPlaceLoading] = useState(false);
  const [bbox, setBbox] = useState<BBox>(BINGHAM_CANYON_BBOX);
  const [bboxDraft, setBboxDraft] = useState(BINGHAM_CANYON_BBOX.join(", "));
  const [providers, setProviders] = useState<ProviderId[]>([
    "umbra",
    "sentinel-1",
  ]);
  const [startAt, setStartAt] = useState("2025-06-01");
  const [endAt, setEndAt] = useState("2025-08-01");
  const [productType, setProductType] = useState("");
  const [polarization, setPolarization] = useState("");
  const [maxResolution, setMaxResolution] = useState("");
  const [response, setResponse] = useState<CatalogSearchResponse | null>(null);
  const [status, setStatus] = useState<
    "idle" | "loading" | "ready" | "error" | "stale"
  >("idle");
  const [error, setError] = useState<string | null>(null);
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [pair, setPair] = useState<Pair>({ before: null, after: null });
  const [reviewOpen, setReviewOpen] = useState(false);
  const [editingAoi, setEditingAoi] = useState(false);
  const [drawingStep, setDrawingStep] = useState<
    "awaiting-first" | "awaiting-second"
  >("awaiting-first");
  const controller = useRef<AbortController | null>(null);
  const reviewButton = useRef<HTMLButtonElement>(null);
  const drawButton = useRef<HTMLButtonElement>(null);
  const bboxInput = useRef<HTMLTextAreaElement>(null);

  const selected =
    response?.results.find((item) => itemKey(item) === selectedKey) ?? null;
  const configuredPlaceProvider =
    basemap.deployment === "private-r-and-d"
      ? {
          label: "MapTiler Geocoding",
          attributionUrl: "https://www.maptiler.com/copyright/",
        }
      : {
          label: "OpenStreetMap Nominatim",
          attributionUrl: "https://www.openstreetmap.org/copyright",
        };
  const resultSummary = useMemo(
    () =>
      response?.providers
        .map(
          (report) =>
            `${report.result_count} ${formatProvider(report.provider)}`,
        )
        .join(" · ") ?? "Search to load provider metadata",
    [response],
  );

  const resolvePlace = async () => {
    setPlaceLoading(true);
    try {
      const place = await places.resolve(query);
      const nextBbox = validateBbox(place.bbox);
      setPlaceLabel(place.label);
      setPlaceSource({
        provider: place.provider,
        attributionUrl: place.attributionUrl,
      });
      setBbox(nextBbox);
      setBboxDraft(nextBbox.join(", "));
      if (response) setStatus("stale");
      setError(null);
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Place lookup failed.",
      );
    } finally {
      setPlaceLoading(false);
    }
  };

  const applyBbox = () => {
    try {
      const next = validateBbox(
        bboxDraft.split(",").map((part) => Number(part.trim())),
      );
      setBbox(next);
      setPlaceLabel("Custom WGS84 AOI");
      if (response) setStatus("stale");
      setError(null);
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "The AOI is invalid.",
      );
    }
  };

  const acceptDrawnBbox = useCallback((next: BBox) => {
    try {
      const validated = validateBbox(next);
      setBbox(validated);
      setBboxDraft(validated.map((value) => value.toFixed(5)).join(", "));
      setPlaceLabel("Map-drawn WGS84 AOI");
      setEditingAoi(false);
      setDrawingStep("awaiting-first");
      setStatus((current) => (current === "ready" ? "stale" : current));
      setError(null);
      queueMicrotask(() => bboxInput.current?.focus());
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "The drawn AOI is invalid.",
      );
    }
  }, []);

  const cancelDrawing = useCallback(() => {
    setEditingAoi(false);
    setDrawingStep("awaiting-first");
    queueMicrotask(() => drawButton.current?.focus());
  }, []);

  useEffect(() => {
    if (!editingAoi) return;
    const cancel = (event: globalThis.KeyboardEvent) => {
      if (event.key === "Escape") cancelDrawing();
    };
    window.addEventListener("keydown", cancel);
    return () => window.removeEventListener("keydown", cancel);
  }, [cancelDrawing, editingAoi]);

  const search = async () => {
    if (providers.length === 0) {
      setError("Select at least one imagery provider.");
      return;
    }
    controller.current?.abort();
    controller.current = new AbortController();
    setStatus("loading");
    setError(null);
    const activeController = controller.current;
    const baseRequest = {
      contract_version: "1.0.0" as const,
      aoi: { bbox, geometry: polygonFromBbox(bbox) },
      start_at: `${startAt}T00:00:00Z`,
      end_at: `${endAt}T23:59:59Z`,
      product_types: productType ? [productType] : [],
      polarizations: polarization ? polarization.split("+") : [],
      max_resolution_m: maxResolution ? Number(maxResolution) : null,
      page_size: 25,
      cursor: null,
    };
    const settled = await Promise.allSettled(
      providers.map((provider) =>
        catalog.search(
          {
            ...baseRequest,
            providers: [provider],
          },
          activeController.signal,
        ),
      ),
    );
    if (activeController.signal.aborted) return;

    const results: CatalogItem[] = [];
    const reports: ProviderReport[] = [];
    const warnings: CatalogWarning[] = [];
    const queryIds: string[] = [];
    let latestGeneratedAt = "";
    let allCacheHits = true;
    let sampledResultCount = 0;
    let failedCount = 0;

    settled.forEach((outcome, index) => {
      const provider = providers[index];
      if (outcome.status === "fulfilled") {
        const providerResponse = outcome.value;
        results.push(...providerResponse.results);
        reports.push(...providerResponse.providers);
        warnings.push(...providerResponse.warnings);
        queryIds.push(providerResponse.query_id);
        sampledResultCount += providerResponse.sampled_result_count;
        allCacheHits &&= providerResponse.cache === "hit";
        if (providerResponse.generated_at > latestGeneratedAt) {
          latestGeneratedAt = providerResponse.generated_at;
        }
        return;
      }
      failedCount += 1;
      const detail =
        outcome.reason instanceof Error
          ? outcome.reason.message
          : "The provider request did not complete.";
      const kind =
        outcome.reason instanceof CatalogClientError
          ? outcome.reason.kind
          : "unknown";
      reports.push({
        provider,
        status: "failed",
        result_count: 0,
        has_more: false,
        warning_count: 1,
      });
      warnings.push({
        code: `provider_${kind.replace("-", "_")}`,
        provider,
        retryable: kind !== "permission",
        message: `${formatProvider(provider)} did not complete: ${detail}`,
      });
    });

    const uniqueResults = [
      ...new Map(results.map((item) => [itemKey(item), item])).values(),
    ].sort(
      (left, right) =>
        new Date(right.acquired_at).getTime() -
        new Date(left.acquired_at).getTime(),
    );
    const partial =
      failedCount > 0 || reports.some((report) => report.status !== "complete");
    const result: CatalogSearchResponse = {
      contract_version: "1.0.0",
      query_id: queryIds.join(":") || "provider-search-failed",
      status: partial
        ? "partial"
        : uniqueResults.length > 0
          ? "complete"
          : "empty",
      generated_at: latestGeneratedAt || new Date().toISOString(),
      cache: allCacheHits && failedCount === 0 ? "hit" : "miss",
      results: uniqueResults,
      providers: reports,
      warnings,
      next_cursor: null,
      sampled_result_count: sampledResultCount,
    };
    setResponse(result);
    setSelectedKey(result.results[0] ? itemKey(result.results[0]) : null);
    if (failedCount === providers.length) {
      setStatus("error");
      setError(
        "No selected provider completed. Check the local API or retry a provider.",
      );
    } else {
      setStatus("ready");
    }
  };

  const cancelSearch = () => {
    controller.current?.abort();
    setStatus(response ? "ready" : "idle");
    setError(null);
  };

  const toggleProvider = (provider: ProviderId) => {
    setProviders((current) =>
      current.includes(provider)
        ? current.filter((item) => item !== provider)
        : [...current, provider],
    );
    if (response) setStatus("stale");
  };

  const select = useCallback((key: string) => setSelectedKey(key), []);
  const assign = (slot: keyof Pair, item: CatalogItem) => {
    const other = slot === "before" ? pair.after : pair.before;
    if (other && itemKey(other) === itemKey(item)) {
      setError("Choose two distinct acquisitions for Before and After.");
      return;
    }
    setPair((current) => ({ ...current, [slot]: item }));
    setError(null);
  };

  return (
    <div className="explore-shell">
      <a className="skip-link" href="#acquisition-results">
        Skip to acquisition results
      </a>
      <header className="explore-header">
        <div className="mission-brand">
          <span className="brand-mark" aria-hidden="true">
            EA
          </span>
          <strong>EchoAtlas</strong>
        </div>
        <nav aria-label="Primary">
          <button aria-current="page">Explore</button>
          <button onClick={onAnalyze}>
            Analyze{" "}
            <span>
              · {pair.before && pair.after ? "pair retained" : "no pair"}
            </span>
          </button>
        </nav>
        <span className="status-pill status-success">
          Civilian research use
        </span>
      </header>

      <section className="explore-search-band" aria-labelledby="explore-title">
        <div>
          <p className="overline">Global imagery discovery</p>
          <h1 id="explore-title">Explore provider-reported SAR availability</h1>
          <p>
            Navigate anywhere. Availability appears only where a provider
            reports an acquisition footprint.
          </p>
        </div>
        <form
          role="search"
          onSubmit={(event) => {
            event.preventDefault();
            void resolvePlace();
          }}
        >
          <label htmlFor="place-search">Place or latitude, longitude</label>
          <div>
            <input
              id="place-search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
            <button type="submit" disabled={placeLoading}>
              {placeLoading ? "Finding…" : "Go"}
            </button>
          </div>
          <small>
            Place names go to {configuredPlaceProvider.label} only when you
            press Go; coordinates resolve locally.{" "}
            <a
              href={configuredPlaceProvider.attributionUrl}
              target="_blank"
              rel="noreferrer"
            >
              Attribution
            </a>
            .
          </small>
          <small>
            Current AOI source: {placeSource.provider}
            {placeSource.attributionUrl ? (
              <>
                {" · "}
                <a
                  href={placeSource.attributionUrl}
                  target="_blank"
                  rel="noreferrer"
                >
                  source terms
                </a>
              </>
            ) : null}
          </small>
        </form>
      </section>

      <section
        className="explore-boundary"
        aria-label="Coverage and interpretation boundary"
      >
        <span aria-hidden="true">i</span>
        <p>
          <strong>The globe is navigation—not imagery coverage.</strong>{" "}
          Outlines are provider-reported acquisitions. A candidate pair still
          requires comparability review before processing.
        </p>
      </section>
      {error && (
        <section className="explore-state state-error" role="alert">
          <strong>
            {status === "error"
              ? "Catalog search is offline"
              : "Search needs attention"}
          </strong>
          <span>{error}</span>
        </section>
      )}
      {status === "loading" && (
        <section className="explore-state" aria-live="polite">
          <strong>Searching bounded provider metadata</strong>
          <span>No raster imagery is downloading.</span>
          <button onClick={cancelSearch}>Cancel</button>
        </section>
      )}
      {status === "stale" && (
        <section className="explore-state" aria-live="polite">
          <strong>Results are stale for this draft</strong>
          <span>
            Search again to apply the changed area or provider filters.
          </span>
        </section>
      )}

      <main className="explore-grid-live">
        <aside className="explore-query panel" aria-labelledby="query-title">
          <div className="panel-heading">
            <div>
              <p className="overline">Search definition</p>
              <h2 id="query-title">Area and filters</h2>
            </div>
          </div>
          <section className="explore-aoi">
            <h3>{placeLabel}</h3>
            <span>Rectangle · WGS84</span>
            <label htmlFor="bbox">West, south, east, north</label>
            <textarea
              id="bbox"
              ref={bboxInput}
              value={bboxDraft}
              onChange={(event) => setBboxDraft(event.target.value)}
            />
            <button onClick={applyBbox}>Apply exact AOI</button>
            <button
              ref={drawButton}
              aria-pressed={editingAoi}
              onClick={() => {
                setDrawingStep("awaiting-first");
                setEditingAoi(true);
              }}
            >
              Draw AOI on map
            </button>
            <button
              onClick={() => {
                setBbox(BINGHAM_CANYON_BBOX);
                setBboxDraft(BINGHAM_CANYON_BBOX.join(", "));
                setPlaceLabel("Bingham Canyon, Utah");
                setPlaceSource({
                  provider: "Preset AOI",
                  attributionUrl: null,
                });
                if (response) setStatus("stale");
                setError(null);
              }}
            >
              Reset
            </button>
          </section>
          <fieldset>
            <legend>Providers</legend>
            {(["umbra", "sentinel-1"] as ProviderId[]).map((provider) => (
              <label key={provider}>
                <input
                  type="checkbox"
                  checked={providers.includes(provider)}
                  onChange={() => toggleProvider(provider)}
                />{" "}
                {formatProvider(provider)}
              </label>
            ))}
          </fieldset>
          <fieldset>
            <legend>Date range</legend>
            <label>
              From
              <input
                type="date"
                value={startAt}
                onChange={(event) => {
                  setStartAt(event.target.value);
                  if (response) setStatus("stale");
                }}
              />
            </label>
            <label>
              To
              <input
                type="date"
                value={endAt}
                onChange={(event) => {
                  setEndAt(event.target.value);
                  if (response) setStatus("stale");
                }}
              />
            </label>
          </fieldset>
          <fieldset>
            <legend>Acquisition filters</legend>
            <label>
              Product
              <select
                value={productType}
                onChange={(event) => {
                  setProductType(event.target.value);
                  if (response) setStatus("stale");
                }}
              >
                <option value="">All reported products</option>
                <option value="GRD">GRD</option>
                <option value="GEC">GEC</option>
              </select>
            </label>
            <label>
              Polarization
              <select
                value={polarization}
                onChange={(event) => {
                  setPolarization(event.target.value);
                  if (response) setStatus("stale");
                }}
              >
                <option value="">Any reported polarization</option>
                <option value="VV+VH">VV + VH</option>
                <option value="HH">HH</option>
              </select>
            </label>
            <label>
              Maximum resolution
              <select
                value={maxResolution}
                onChange={(event) => {
                  setMaxResolution(event.target.value);
                  if (response) setStatus("stale");
                }}
              >
                <option value="">Any reported resolution</option>
                <option value="10">10 m</option>
                <option value="5">5 m</option>
                <option value="1">1 m</option>
              </select>
            </label>
          </fieldset>
          <button
            className="primary-button"
            onClick={() => void search()}
            disabled={status === "loading"}
          >
            Search reported acquisitions
          </button>
          <p className="explore-note">
            Search is bounded to this AOI and date range. No raster imagery is
            downloaded.
          </p>
        </aside>

        <section
          className="explore-results panel"
          id="acquisition-results"
          aria-labelledby="results-title"
        >
          <div className="panel-heading">
            <div>
              <p className="overline">Equivalent non-map path</p>
              <h2 id="results-title">
                {response?.results.length ?? 0} reported{" "}
                {response?.results.length === 1
                  ? "acquisition"
                  : "acquisitions"}
              </h2>
            </div>
          </div>
          <p className="explore-result-summary">{resultSummary}</p>
          {response && (
            <ul
              className="provider-reports"
              aria-label="Provider search status"
            >
              {response.providers.map((report, index) => (
                <li key={`${report.provider}:${index}`}>
                  <strong>{formatProvider(report.provider)}</strong>
                  <span>
                    {report.status} · {report.result_count} records
                    {report.has_more ? " · sampled" : ""}
                  </span>
                </li>
              ))}
            </ul>
          )}
          {response?.warnings.map((warning) => (
            <p
              className="provider-warning"
              key={`${warning.provider ?? "catalog"}:${warning.code}`}
            >
              {warning.message}
            </p>
          ))}
          {response?.status === "empty" && (
            <div className="explore-empty">
              <h3>No provider reported coverage for this query</h3>
              <p>
                This does not mean the area was never imaged. Try a wider date
                range, another provider, or a different AOI.
              </p>
            </div>
          )}
          <ol className="acquisition-list">
            {response?.results.map((item) => {
              const key = itemKey(item);
              return (
                <li key={key}>
                  <article
                    aria-current={key === selectedKey ? "true" : undefined}
                  >
                    <button
                      className="acquisition-select"
                      onClick={() => select(key)}
                    >
                      <strong>
                        {formatProvider(item.provider)} ·{" "}
                        {new Date(item.acquired_at).toLocaleDateString()}
                      </strong>
                      <span>
                        {item.source.collection} ·{" "}
                        {item.product_type ?? "Product not reported"}
                      </span>
                    </button>
                    <dl>
                      <div>
                        <dt>Resolution</dt>
                        <dd>
                          {item.resolution_range_m
                            ? `${item.resolution_range_m} m range`
                            : "Not reported"}
                        </dd>
                      </div>
                      <div>
                        <dt>Polarization</dt>
                        <dd>
                          {item.polarizations.join(" + ") || "Not reported"}
                        </dd>
                      </div>
                      <div>
                        <dt>License</dt>
                        <dd>{item.license.label}</dd>
                      </div>
                    </dl>
                    <div className="acquisition-actions">
                      <button
                        onClick={() => assign("before", item)}
                        aria-label={`Use ${item.source.item_id} as Before`}
                      >
                        Use as Before
                      </button>
                      <button
                        onClick={() => assign("after", item)}
                        aria-label={`Use ${item.source.item_id} as After`}
                      >
                        Use as After
                      </button>
                      <a
                        href={item.source.href}
                        target="_blank"
                        rel="noreferrer"
                      >
                        Source metadata
                      </a>
                    </div>
                  </article>
                </li>
              );
            })}
          </ol>
        </section>

        <section className="explore-map panel" aria-labelledby="map-title">
          <div className="panel-heading">
            <div>
              <p className="overline">Navigation surface</p>
              <h2 id="map-title">Map and reported footprints</h2>
            </div>
          </div>
          <div
            className="explore-map-stage"
            role="region"
            aria-label={`Map centered on ${placeLabel}. Every acquisition remains available in the results list.`}
          >
            {renderMap ? (
              <MapSurface
                bbox={bbox}
                items={response?.results ?? []}
                selectedKey={selectedKey}
                onSelect={select}
                editing={editingAoi}
                onDraw={acceptDrawnBbox}
                onDrawingStepChange={setDrawingStep}
                basemap={basemap}
              />
            ) : (
              <div className="map-test-surface">
                Map renderer omitted in test
              </div>
            )}
            <div className="explore-legend">
              <span className="legend-sentinel">Sentinel-1</span>
              <span className="legend-umbra">Umbra</span>
              <span>Search AOI</span>
            </div>
            {editingAoi && (
              <div className="draw-help" role="status">
                <strong>Draw AOI</strong>
                <p>
                  {drawingStep === "awaiting-first"
                    ? "Select the first corner, then its opposite corner."
                    : "First corner set. Select the opposite corner."}{" "}
                  Escape cancels. Exact coordinates remain available.
                </p>
                <button onClick={cancelDrawing}>Cancel drawing</button>
              </div>
            )}
          </div>
          <footer>
            Basemap: {basemap.label} ·{" "}
            {basemap.deployment === "development"
              ? "local development fallback"
              : "private R&D deployment"}{" "}
            · Renderer: MapLibre · Footprints: provider-reported metadata ·{" "}
            <a href={basemap.attributionUrl} target="_blank" rel="noreferrer">
              attribution
            </a>
          </footer>
        </section>

        <aside className="pair-tray panel" aria-labelledby="pair-title">
          <div className="panel-heading">
            <div>
              <p className="overline">Draft selection</p>
              <h2 id="pair-title">Candidate pair</h2>
            </div>
          </div>
          <PairSlot
            label="Before"
            item={pair.before}
            onClear={() => setPair((current) => ({ ...current, before: null }))}
          />
          <PairSlot
            label="After"
            item={pair.after}
            onClear={() => setPair((current) => ({ ...current, after: null }))}
          />
          {selected && (
            <p className="selected-detail">
              Selected: {selected.source.item_id}
            </p>
          )}
          <p className="pair-warning">
            Machine-selected inputs, not a valid scientific pair.
          </p>
          <button
            ref={reviewButton}
            className="primary-button"
            disabled={!pair.before || !pair.after}
            onClick={() => setReviewOpen(true)}
          >
            Review pair
          </button>
          <p className="explore-note">
            Comparability and processing arrive in EAT-019.
          </p>
        </aside>
      </main>
      {reviewOpen && pair.before && pair.after && (
        <PairReviewDialog
          before={pair.before}
          after={pair.after}
          returnFocus={reviewButton}
          onClose={() => setReviewOpen(false)}
        />
      )}
    </div>
  );
}

function PairSlot({
  label,
  item,
  onClear,
}: {
  label: string;
  item: CatalogItem | null;
  onClear: () => void;
}) {
  return (
    <section className="pair-slot">
      <span>{label}</span>
      {item ? (
        <>
          <strong>
            {formatProvider(item.provider)} · {item.source.item_id}
          </strong>
          <time dateTime={item.acquired_at}>
            {new Date(item.acquired_at).toLocaleString()}
          </time>
          <button onClick={onClear}>Clear {label}</button>
        </>
      ) : (
        <p>No acquisition selected</p>
      )}
    </section>
  );
}

function PairReviewDialog({
  before,
  after,
  returnFocus,
  onClose,
}: {
  before: CatalogItem;
  after: CatalogItem;
  returnFocus: RefObject<HTMLButtonElement | null>;
  onClose: () => void;
}) {
  const heading = useRef<HTMLHeadingElement>(null);
  const dialog = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const focusTarget = returnFocus.current;
    heading.current?.focus();
    return () => focusTarget?.focus();
  }, [returnFocus]);

  const handleKeyDown = (event: KeyboardEvent) => {
    if (event.key === "Escape") {
      event.preventDefault();
      onClose();
      return;
    }
    if (event.key !== "Tab" || dialog.current === null) return;
    const controls = [
      ...dialog.current.querySelectorAll<HTMLElement>(
        "button:not(:disabled), a[href]",
      ),
    ];
    if (controls.length === 0) return;
    const first = controls[0];
    const last = controls[controls.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  };

  return (
    <div className="explore-dialog-backdrop">
      <div
        className="explore-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="pair-review-title"
        ref={dialog}
        onKeyDown={handleKeyDown}
      >
        <div className="explore-dialog-heading">
          <div>
            <p className="overline">Metadata review · no processing</p>
            <h2 id="pair-review-title" ref={heading} tabIndex={-1}>
              Review candidate pair
            </h2>
          </div>
          <button onClick={onClose} aria-label="Close pair review">
            Close
          </button>
        </div>
        <p className="pair-dialog-warning">
          Machine-selected inputs, not a valid scientific pair.
        </p>
        <div className="pair-review-grid">
          <PairReviewItem label="Before" item={before} />
          <PairReviewItem label="After" item={after} />
        </div>
        <p className="explore-note">
          EAT-019 will compare geometry, product, polarization, resolution,
          orbit, and timing before a processing manifest can be created.
        </p>
        <button className="primary-button" disabled>
          Check comparability · EAT-019
        </button>
      </div>
    </div>
  );
}

function PairReviewItem({ label, item }: { label: string; item: CatalogItem }) {
  return (
    <article>
      <p className="overline">{label}</p>
      <h3>
        {formatProvider(item.provider)} · {item.source.item_id}
      </h3>
      <dl>
        <div>
          <dt>Acquired</dt>
          <dd>{new Date(item.acquired_at).toLocaleString()}</dd>
        </div>
        <div>
          <dt>Collection</dt>
          <dd>{item.source.collection}</dd>
        </div>
        <div>
          <dt>Product</dt>
          <dd>{item.product_type ?? "Not reported"}</dd>
        </div>
        <div>
          <dt>Polarization</dt>
          <dd>{item.polarizations.join(" + ") || "Not reported"}</dd>
        </div>
        <div>
          <dt>Resolution</dt>
          <dd>
            {item.resolution_range_m
              ? `${item.resolution_range_m} m range`
              : "Not reported"}
          </dd>
        </div>
        <div>
          <dt>Orbit</dt>
          <dd>{item.orbit_state ?? "Not reported"}</dd>
        </div>
        <div>
          <dt>License</dt>
          <dd>{item.license.label}</dd>
        </div>
      </dl>
      <a href={item.source.href} target="_blank" rel="noreferrer">
        Open provider metadata
      </a>
    </article>
  );
}
