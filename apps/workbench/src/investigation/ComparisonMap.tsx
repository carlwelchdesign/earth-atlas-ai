import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { Map as MapLibreMap, StyleSpecification } from "maplibre-gl";

import type { InvestigationCase } from "./model";
import { caseBounds, copyCamera, isInsideCoverage } from "./map-utils";

export type ComparisonMode = "side-by-side" | "swipe" | "before" | "after";

function observationCollection(investigation: InvestigationCase) {
  return {
    type: "FeatureCollection" as const,
    features: investigation.observations.map((observation) => ({
      type: "Feature" as const,
      id: observation.id,
      geometry: observation.geometry,
      properties: { id: observation.id, title: observation.title },
    })),
  };
}

function mapStyle(
  investigation: InvestigationCase,
  role: "before" | "after",
): StyleSpecification {
  const acquisition = investigation.acquisitions.find(
    (entry) => entry.role === role,
  );
  if (!acquisition) throw new Error(`Missing ${role} acquisition.`);
  const caseBoundary = caseBounds(investigation);
  const bounds = caseBoundary.flat() as [number, number, number, number];
  const imagery = acquisition.imageUrl
    ? {
        type: "image" as const,
        url: acquisition.imageUrl,
        coordinates: [
          [bounds[0], bounds[3]],
          [bounds[2], bounds[3]],
          [bounds[2], bounds[1]],
          [bounds[0], bounds[1]],
        ] as [
          [number, number],
          [number, number],
          [number, number],
          [number, number],
        ],
      }
    : {
        type: "raster" as const,
        tiles: [acquisition.tileTemplate ?? ""],
        tileSize: 256,
        minzoom: 8,
        maxzoom: 14,
        bounds,
        attribution: "Contains modified Copernicus Sentinel data (2026)",
      };
  return {
    version: 8,
    sources: {
      basemap: {
        type: "raster",
        tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
        tileSize: 256,
        attribution: "© OpenStreetMap contributors",
      },
      imagery,
      coverage: {
        type: "geojson",
        data: {
          type: "Feature",
          properties: {},
          geometry: investigation.coverage,
        },
      },
      observations: {
        type: "geojson",
        data: observationCollection(investigation),
      },
    },
    layers: [
      {
        id: "basemap",
        type: "raster",
        source: "basemap",
        paint: { "raster-opacity": 0.38 },
      },
      { id: "imagery", type: "raster", source: "imagery" },
      {
        id: "observation-fill",
        type: "fill",
        source: "observations",
        paint: { "fill-color": "#ffb84d", "fill-opacity": 0.18 },
      },
      {
        id: "observation-line",
        type: "line",
        source: "observations",
        paint: { "line-color": "#ffcf70", "line-width": 2.5 },
      },
      {
        id: "coverage-line",
        type: "line",
        source: "coverage",
        paint: {
          "line-color": "#78e3d0",
          "line-width": 3,
          "line-dasharray": [2, 1.25],
        },
      },
    ],
  };
}

function StaticComparison({
  investigation,
}: {
  investigation: InvestigationCase;
}) {
  return (
    <div
      className="static-comparison"
      aria-label="Static before and after comparison"
    >
      {investigation.acquisitions.map((acquisition) => (
        <figure key={acquisition.role}>
          <img
            src={acquisition.thumbnail}
            alt={`${acquisition.role === "before" ? "Before" : "After"} Sentinel-2 view of the prepared Nepal corridor`}
          />
          <figcaption>
            {acquisition.role === "before" ? "Before" : "After"} ·{" "}
            {new Date(acquisition.acquiredAt).toLocaleDateString("en-US", {
              month: "short",
              day: "numeric",
              year: "numeric",
              timeZone: "UTC",
            })}
          </figcaption>
        </figure>
      ))}
    </div>
  );
}

export function ComparisonMap({
  investigation,
  selectedObservationId,
  onSelectObservation,
  renderMap = true,
}: {
  investigation: InvestigationCase;
  selectedObservationId: string | null;
  onSelectObservation: (id: string) => void;
  renderMap?: boolean;
}) {
  const beforeContainer = useRef<HTMLDivElement>(null);
  const afterContainer = useRef<HTMLDivElement>(null);
  const maps = useRef<{ before: MapLibreMap; after: MapLibreMap } | null>(null);
  const retainedCamera = useRef<{
    center: [number, number];
    zoom: number;
  } | null>(null);
  const synchronizing = useRef(false);
  const [mode, setMode] = useState<ComparisonMode>("side-by-side");
  const [swipe, setSwipe] = useState(50);
  const [status, setStatus] = useState("Prepared coverage loaded.");
  const [mapFailed, setMapFailed] = useState(false);
  const bounds = useMemo(() => caseBounds(investigation), [investigation]);

  useEffect(() => {
    if (!renderMap) return;
    let active = true;
    void import("maplibre-gl")
      .then(({ Map, NavigationControl }) => {
        if (!active || !beforeContainer.current || !afterContainer.current)
          return;
        const options = (
          role: "before" | "after",
          container: HTMLDivElement,
        ) => {
          const camera = retainedCamera.current;
          return {
            container,
            style: mapStyle(investigation, role),
            ...(camera
              ? { center: camera.center, zoom: camera.zoom }
              : { bounds, fitBoundsOptions: { padding: 44, animate: false } }),
            dragRotate: false,
            pitchWithRotate: false,
            keyboard: true,
            maxPitch: 0,
            bearing: 0,
            cooperativeGestures: true,
            attributionControl: {},
          };
        };
        const before = new Map(options("before", beforeContainer.current));
        const after = new Map(options("after", afterContainer.current));
        before.addControl(
          new NavigationControl({ showCompass: false }),
          "top-right",
        );
        after.addControl(
          new NavigationControl({ showCompass: false }),
          "top-right",
        );
        maps.current = { before, after };

        const sync = (source: MapLibreMap, target: MapLibreMap) => {
          if (synchronizing.current) return;
          synchronizing.current = true;
          copyCamera(source, target);
          synchronizing.current = false;
          const center = source.getCenter();
          setStatus(
            isInsideCoverage(center.lng, center.lat, investigation)
              ? "Viewing prepared coverage. Selected acquisitions remain fixed until you choose another date."
              : "Map center is outside prepared coverage.",
          );
        };
        before.on("move", () => sync(before, after));
        after.on("move", () => sync(after, before));
        for (const map of [before, after]) {
          map.on("click", "observation-fill", (event) => {
            const properties: unknown = event.features?.[0]?.properties;
            const id =
              typeof properties === "object" &&
              properties !== null &&
              "id" in properties
                ? properties.id
                : null;
            if (typeof id === "string") onSelectObservation(id);
          });
          map.on("mouseenter", "observation-fill", () => {
            map.getCanvas().style.cursor = "pointer";
          });
          map.on("mouseleave", "observation-fill", () => {
            map.getCanvas().style.cursor = "";
          });
          map.on("error", (event) => {
            if ("sourceId" in event && event.sourceId === "imagery") {
              setStatus(
                "A prepared imagery tile is unavailable. Static comparison remains available.",
              );
            }
          });
        }
      })
      .catch(() => setMapFailed(true));
    return () => {
      active = false;
      if (maps.current) {
        const center = maps.current.before.getCenter();
        retainedCamera.current = {
          center: [center.lng, center.lat],
          zoom: maps.current.before.getZoom(),
        };
      }
      maps.current?.before.remove();
      maps.current?.after.remove();
      maps.current = null;
    };
  }, [bounds, investigation, onSelectObservation, renderMap]);

  useEffect(() => {
    const selected = investigation.observations.find(
      (observation) => observation.id === selectedObservationId,
    );
    if (!selected || !maps.current) return;
    for (const map of [maps.current.before, maps.current.after]) {
      map.easeTo({
        center: selected.focus,
        zoom: Math.max(map.getZoom(), 13),
        bearing: 0,
        pitch: 0,
      });
      map.setPaintProperty("observation-fill", "fill-opacity", [
        "case",
        ["==", ["get", "id"], selected.id],
        0.42,
        0.18,
      ]);
      map.setPaintProperty("observation-line", "line-width", [
        "case",
        ["==", ["get", "id"], selected.id],
        4.5,
        2.5,
      ]);
    }
  }, [investigation.observations, selectedObservationId]);

  useEffect(() => {
    window.setTimeout(() => {
      maps.current?.before.resize();
      maps.current?.after.resize();
    }, 0);
  }, [mode, swipe]);

  const returnToExtent = useCallback(() => {
    if (!maps.current) return;
    synchronizing.current = true;
    maps.current.before.fitBounds(bounds, { padding: 44, animate: false });
    maps.current.after.fitBounds(bounds, { padding: 44, animate: false });
    synchronizing.current = false;
    setStatus("Returned to prepared case extent.");
  }, [bounds]);

  const fallback = !renderMap || mapFailed;
  return (
    <section className="comparison-map" aria-labelledby="comparison-heading">
      <div className="comparison-heading-row">
        <div>
          <p className="eyebrow">Geographic comparison</p>
          <h2 id="comparison-heading">Selected dates, shared camera</h2>
        </div>
        <button
          type="button"
          className="secondary-button"
          onClick={returnToExtent}
        >
          Return to case extent
        </button>
      </div>
      <div
        className="comparison-controls"
        role="group"
        aria-label="Comparison mode"
      >
        {(["side-by-side", "swipe", "before", "after"] as const).map(
          (option) => (
            <button
              type="button"
              key={option}
              aria-pressed={mode === option}
              onClick={() => setMode(option)}
            >
              {option === "side-by-side"
                ? "Side by side"
                : option === "swipe"
                  ? "Swipe"
                  : option[0].toUpperCase() + option.slice(1)}
            </button>
          ),
        )}
      </div>
      {mode === "swipe" ? (
        <div className="swipe-control">
          <label htmlFor="after-image-reveal">After-image reveal</label>
          <input
            id="after-image-reveal"
            type="range"
            min="0"
            max="100"
            value={swipe}
            onChange={(event) => setSwipe(Number(event.currentTarget.value))}
          />
          <span>{swipe}% after</span>
        </div>
      ) : null}
      <div
        className={`comparison-frame mode-${mode}${fallback ? " is-fallback" : ""}`}
      >
        {!renderMap || mapFailed ? (
          <StaticComparison investigation={investigation} />
        ) : null}
        <div
          className="map-panel before-panel"
          aria-label="Before satellite map"
        >
          <span className="map-date">
            Before ·{" "}
            {formatAcquisitionDate(investigation.acquisitions[0].acquiredAt)}
          </span>
          <div className="investigation-map-canvas" ref={beforeContainer} />
        </div>
        <div
          className="map-panel after-panel"
          aria-label="After satellite map"
          style={
            mode === "swipe"
              ? { clipPath: `inset(0 0 0 ${100 - swipe}%)` }
              : undefined
          }
        >
          <span className="map-date">
            After ·{" "}
            {formatAcquisitionDate(investigation.acquisitions[1].acquiredAt)}
          </span>
          <div className="investigation-map-canvas" ref={afterContainer} />
        </div>
      </div>
      <p className="map-status" role="status" aria-live="polite">
        {fallback
          ? "Interactive map unavailable. The static comparison and observation list remain usable."
          : status}
      </p>
    </section>
  );
}

function formatAcquisitionDate(timestamp: string) {
  return new Date(timestamp).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC",
  });
}
