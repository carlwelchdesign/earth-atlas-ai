import { describe, expect, it } from "vitest";

import { selectBasemap } from "./basemap";

describe("basemap selection", () => {
  it("uses the bounded public OSM fallback only without a deployment key", () => {
    const basemap = selectBasemap();

    expect(basemap.deployment).toBe("public-low-traffic");
    expect(basemap.label).toBe("OpenStreetMap standard tiles");
    expect(typeof basemap.style).toBe("object");
  });

  it("selects the MapTiler private R&D adapter when configured", () => {
    const basemap = selectBasemap("test key");

    expect(basemap.deployment).toBe("private-r-and-d");
    expect(basemap.label).toBe("MapTiler Dataviz");
    expect(basemap.style).toBe(
      "https://api.maptiler.com/maps/dataviz/style.json?key=test%20key",
    );
  });
});
