import { afterEach, describe, expect, it, vi } from "vitest";

import { HttpNepalImageryClient } from "./imagery";

afterEach(() => vi.unstubAllGlobals());

describe("Nepal imagery client", () => {
  it("accepts only the bounded prepared manifest and approved image path", async () => {
    const request = vi.fn(() =>
      Promise.resolve(
        new Response(
          JSON.stringify({
            maximum_range_days: 60,
            acquisitions: [
              {
                item_id: "S2B_45RUM_20260906_0_L2A",
                product_id: "S2B_MSIL2A_20260906_TEST.SAFE",
                acquired_at: "2026-09-06T05:10:46Z",
                source_url:
                  "https://earth-search.aws.element84.com/v1/collections/sentinel-2-l2a/items/S2B_45RUM_20260906_0_L2A",
                image_url:
                  "/generated-nepal/acquisitions/S2B_45RUM_20260906_0_L2A.png",
                cloud_cover_percent: 77.9,
                cloud_shadow_percent: 4.5,
                nodata_percent: 9.1,
                crs: "EPSG:32645",
                resolution_metres: 10,
              },
            ],
          }),
          { status: 200, headers: { "content-type": "application/json" } },
        ),
      ),
    );
    vi.stubGlobal("fetch", request);

    const acquisitions = await new HttpNepalImageryClient().listAcquisitions(
      "2026-07-27",
      "2026-09-24",
    );

    expect(request).toHaveBeenCalledWith(
      "/generated-nepal/acquisitions.json?start=2026-07-27&end=2026-09-24",
      expect.objectContaining({ cache: "no-store" }),
    );
    expect(acquisitions[0].imageUrl).toMatch(
      /^\/generated-nepal\/acquisitions/,
    );
  });

  it("rejects a response that weakens the 60-day boundary", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve(
          new Response(
            JSON.stringify({ maximum_range_days: 366, acquisitions: [] }),
            { status: 200 },
          ),
        ),
      ),
    );

    await expect(
      new HttpNepalImageryClient().listAcquisitions("2026-07-27", "2026-09-24"),
    ).rejects.toThrow("60-day boundary");
  });
});
