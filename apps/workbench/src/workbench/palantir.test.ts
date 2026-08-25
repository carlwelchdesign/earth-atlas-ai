import { describe, expect, it, vi } from "vitest";

import {
  initialPlatformConnectionState,
  loadPalantirConnectionState,
  type PalantirProbeConfig,
} from "./palantir";

const hostedLocation = {
  hostname:
    "echoatlas-restricted-test-teae6zflavlbtz3q.apps.usw-3.palantirfoundry.com",
  origin:
    "https://echoatlas-restricted-test-teae6zflavlbtz3q.apps.usw-3.palantirfoundry.com",
};

describe("Palantir connection boundary", () => {
  it("keeps every other host on the standalone path", async () => {
    const probe = vi.fn();

    expect(
      initialPlatformConnectionState({
        hostname: "localhost",
        origin: "http://localhost:5173",
      }),
    ).toEqual({ status: "standalone" });
    await expect(
      loadPalantirConnectionState({
        location: {
          hostname: "localhost",
          origin: "http://localhost:5173",
        },
        probe,
      }),
    ).resolves.toEqual({ status: "standalone" });
    expect(probe).not.toHaveBeenCalled();
  });

  it("requests only the configured read operations on the hosted domain", async () => {
    let received: PalantirProbeConfig | undefined;

    expect(initialPlatformConnectionState(hostedLocation)).toEqual({
      status: "connecting",
    });
    await expect(
      loadPalantirConnectionState({
        location: hostedLocation,
        probe: (config) => {
          received = config;
          return Promise.resolve(1);
        },
      }),
    ).resolves.toEqual({
      status: "connected",
      analysisRunAvailable: true,
    });

    expect(received).toMatchObject({
      redirectUrl: `${hostedLocation.origin}/auth/callback`,
      postLoginPage: `${hostedLocation.origin}/`,
      scopes: ["api:use-ontologies-read", "api:use-mediasets-read"],
    });
  });

  it("distinguishes an empty readable object type from a failed connection", async () => {
    await expect(
      loadPalantirConnectionState({
        location: hostedLocation,
        probe: () => Promise.resolve(0),
      }),
    ).resolves.toEqual({
      status: "connected",
      analysisRunAvailable: false,
    });
  });

  it("surfaces an unavailable state without disabling the local bundle", async () => {
    await expect(
      loadPalantirConnectionState({
        location: hostedLocation,
        probe: () => Promise.reject(new Error("Foundry unavailable")),
      }),
    ).resolves.toEqual({
      status: "unavailable",
      reason:
        "The read-only Foundry check did not complete. The validated local bundle remains active.",
    });
  });
});
