import { useEffect, useRef } from "react";
import type { GeoJSONSource, Map as MapLibreMap } from "maplibre-gl";

import { defaultBasemap, type BasemapConfig } from "./basemap";
import type { BBox, CatalogItem } from "./model";
import { itemKey, polygonFromBbox } from "./model";

function featureCollection(items: CatalogItem[]) {
  return {
    type: "FeatureCollection" as const,
    features: items.map((item) => ({
      type: "Feature" as const,
      geometry: item.footprint,
      properties: { key: itemKey(item), provider: item.provider },
    })),
  };
}

export function MapSurface({
  bbox,
  items,
  selectedKey,
  onSelect,
  editing = false,
  onDraw,
  onDrawingStepChange,
  basemap = defaultBasemap(),
}: {
  bbox: BBox;
  items: CatalogItem[];
  selectedKey: string | null;
  onSelect: (key: string) => void;
  editing?: boolean;
  onDraw?: (bbox: BBox) => void;
  onDrawingStepChange?: (step: "awaiting-first" | "awaiting-second") => void;
  basemap?: BasemapConfig;
}) {
  const container = useRef<HTMLDivElement>(null);
  const map = useRef<MapLibreMap | null>(null);
  const itemsRef = useRef(items);
  const selectedKeyRef = useRef(selectedKey);
  const editingRef = useRef(editing);
  const onDrawRef = useRef(onDraw);
  const onDrawingStepChangeRef = useRef(onDrawingStepChange);
  const drawStart = useRef<[number, number] | null>(null);

  useEffect(() => {
    let active = true;
    void import("maplibre-gl").then(({ Map, NavigationControl }) => {
      if (!active || container.current === null || map.current !== null) return;
      const reduceMotion = window.matchMedia(
        "(prefers-reduced-motion: reduce)",
      ).matches;
      const instance = new Map({
        container: container.current,
        style: basemap.style,
        bounds: [
          [bbox[0], bbox[1]],
          [bbox[2], bbox[3]],
        ],
        fitBoundsOptions: { padding: 54, animate: false },
        cooperativeGestures: true,
        dragRotate: false,
        pitchWithRotate: false,
        keyboard: true,
        reduceMotion,
        attributionControl: {},
      });
      instance.addControl(
        new NavigationControl({ showCompass: false }),
        "top-right",
      );
      instance.on("load", () => {
        instance.addSource("search-aoi", {
          type: "geojson",
          data: {
            type: "Feature",
            properties: {},
            geometry: polygonFromBbox(bbox),
          },
        });
        instance.addLayer({
          id: "search-aoi-boundary",
          type: "line",
          source: "search-aoi",
          paint: {
            "line-color": "#60d3bf",
            "line-width": 3,
            "line-dasharray": [2, 1.4],
          },
        });
        instance.addSource("acquisitions", {
          type: "geojson",
          data: featureCollection(itemsRef.current),
        });
        instance.addLayer({
          id: "acquisition-footprints",
          type: "line",
          source: "acquisitions",
          paint: {
            "line-color": [
              "match",
              ["get", "provider"],
              "umbra",
              "#f0b45a",
              "#6da9e8",
            ],
            "line-width": [
              "case",
              ["==", ["get", "key"], selectedKeyRef.current ?? ""],
              5,
              3,
            ],
            "line-dasharray": [
              "match",
              ["get", "provider"],
              "umbra",
              ["literal", [1, 1.4]],
              ["literal", [2.5, 1.2]],
            ],
          },
        });
        instance.on("click", "acquisition-footprints", (event) => {
          if (editingRef.current) return;
          const properties: unknown = event.features?.[0]?.properties;
          const key =
            typeof properties === "object" &&
            properties !== null &&
            "key" in properties
              ? properties.key
              : null;
          if (typeof key === "string") onSelect(key);
        });
        instance.on("click", (event) => {
          if (!editingRef.current) return;
          const point: [number, number] = [event.lngLat.lng, event.lngLat.lat];
          if (drawStart.current === null) {
            drawStart.current = point;
            onDrawingStepChangeRef.current?.("awaiting-second");
            return;
          }
          const [firstLongitude, firstLatitude] = drawStart.current;
          drawStart.current = null;
          const next: BBox = [
            Math.min(firstLongitude, point[0]),
            Math.min(firstLatitude, point[1]),
            Math.max(firstLongitude, point[0]),
            Math.max(firstLatitude, point[1]),
          ];
          if (next[0] !== next[2] && next[1] !== next[3]) {
            onDrawRef.current?.(next);
          }
        });
      });
      map.current = instance;
    });
    return () => {
      active = false;
      map.current?.remove();
      map.current = null;
    };
  }, [basemap.style, bbox, onSelect]);

  useEffect(() => {
    itemsRef.current = items;
    selectedKeyRef.current = selectedKey;
    editingRef.current = editing;
    onDrawRef.current = onDraw;
    onDrawingStepChangeRef.current = onDrawingStepChange;
    if (!editing) drawStart.current = null;
    const instance = map.current;
    if (!instance?.isStyleLoaded()) return;
    const source = instance.getSource<GeoJSONSource>("acquisitions");
    if (source) void source.setData(featureCollection(items));
    if (instance.getLayer("acquisition-footprints")) {
      instance.setPaintProperty("acquisition-footprints", "line-width", [
        "case",
        ["==", ["get", "key"], selectedKey ?? ""],
        5,
        3,
      ]);
    }
  }, [editing, items, onDraw, onDrawingStepChange, selectedKey]);

  return (
    <div
      className={`explore-map-canvas${editing ? " is-editing" : ""}`}
      ref={container}
    />
  );
}
