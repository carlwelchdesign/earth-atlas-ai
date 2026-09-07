import type { Map as MapLibreMap } from "maplibre-gl";

import type { InvestigationCase } from "./model";

export function caseBounds(
  investigation: InvestigationCase,
): [[number, number], [number, number]] {
  const ring = investigation.coverage.coordinates[0];
  return [
    [
      Math.min(...ring.map(([longitude]) => longitude)),
      Math.min(...ring.map(([, latitude]) => latitude)),
    ],
    [
      Math.max(...ring.map(([longitude]) => longitude)),
      Math.max(...ring.map(([, latitude]) => latitude)),
    ],
  ];
}

export function isInsideCoverage(
  longitude: number,
  latitude: number,
  investigation: InvestigationCase,
): boolean {
  const [[west, south], [east, north]] = caseBounds(investigation);
  return (
    longitude >= west &&
    longitude <= east &&
    latitude >= south &&
    latitude <= north
  );
}

export function copyCamera(source: MapLibreMap, target: MapLibreMap): void {
  const center = source.getCenter();
  target.jumpTo({ center, zoom: source.getZoom(), bearing: 0, pitch: 0 });
}
