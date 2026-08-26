import type { StyleSpecification } from "maplibre-gl";

export interface BasemapConfig {
  style: string | StyleSpecification;
  label: string;
  attributionUrl: string;
  deployment: "development" | "private-r-and-d";
}

const osmDevelopmentBasemap: BasemapConfig = {
  style: {
    version: 8,
    sources: {
      "osm-development": {
        type: "raster",
        tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
        tileSize: 256,
        attribution: "© OpenStreetMap contributors",
      },
    },
    layers: [
      {
        id: "osm-development",
        type: "raster",
        source: "osm-development",
      },
    ],
  },
  label: "OpenStreetMap development tiles",
  attributionUrl: "https://www.openstreetmap.org/copyright",
  deployment: "development",
};

export function selectBasemap(mapTilerKey?: string): BasemapConfig {
  const key = mapTilerKey?.trim();
  if (!key) return osmDevelopmentBasemap;
  return {
    style: `https://api.maptiler.com/maps/dataviz/style.json?key=${encodeURIComponent(key)}`,
    label: "MapTiler Dataviz",
    attributionUrl: "https://www.maptiler.com/copyright/",
    deployment: "private-r-and-d",
  };
}

export function defaultBasemap(): BasemapConfig {
  const configuredKey: unknown = import.meta.env.VITE_MAPTILER_API_KEY;
  return selectBasemap(
    typeof configuredKey === "string" ? configuredKey : undefined,
  );
}
