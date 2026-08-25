import type { ObjectTypeDefinition } from "@osdk/api";

const hostedApplicationHostname =
  "echoatlas-restricted-test-teae6zflavlbtz3q.apps.usw-3.palantirfoundry.com";

const palantirApplication = {
  clientId: "ce562c2a3fa3c9ce3a09ee009176d94a", // pragma: allowlist secret
  foundryUrl: "https://earth-atlas-app.usw-3.palantirfoundry.com",
  ontologyRid: "ri.ontology.main.ontology.5cbe2d81-9d9c-4f2e-9a9f-63ba30a77e63",
  scopes: ["api:use-ontologies-read", "api:use-mediasets-read"],
} as const;

interface EchoAtlasAnalysisRun extends ObjectTypeDefinition {
  type: "object";
  apiName: "EchoAtlasAnalysisRun";
}

// TypeScript OSDK 2.x generated object exports use this runtime descriptor.
// Keeping it local avoids requiring the enrollment-private package in public CI.
const EchoAtlasAnalysisRun = {
  type: "object",
  apiName: "EchoAtlasAnalysisRun",
} satisfies EchoAtlasAnalysisRun;

export type PlatformConnectionState =
  | { status: "standalone" }
  | { status: "connecting" }
  | { status: "connected"; analysisRunAvailable: boolean }
  | { status: "unavailable"; reason: string };

export interface PalantirProbeConfig {
  clientId: string;
  foundryUrl: string;
  ontologyRid: string;
  redirectUrl: string;
  postLoginPage: string;
  scopes: readonly string[];
}

export type PalantirProbe = (config: PalantirProbeConfig) => Promise<number>;

interface BrowserLocation {
  hostname: string;
  origin: string;
}

interface PalantirConnectionOptions {
  location?: BrowserLocation;
  probe?: PalantirProbe;
}

export function initialPlatformConnectionState(
  location: BrowserLocation = window.location,
): PlatformConnectionState {
  return isPalantirHostedLocation(location)
    ? { status: "connecting" }
    : { status: "standalone" };
}

export async function loadPalantirConnectionState({
  location = window.location,
  probe = probeAnalysisRuns,
}: PalantirConnectionOptions = {}): Promise<PlatformConnectionState> {
  if (!isPalantirHostedLocation(location)) return { status: "standalone" };

  try {
    const analysisRunCount = await probe({
      ...palantirApplication,
      redirectUrl: `${location.origin}/auth/callback`,
      postLoginPage: `${location.origin}/`,
    });
    return {
      status: "connected",
      analysisRunAvailable: analysisRunCount > 0,
    };
  } catch {
    return {
      status: "unavailable",
      reason:
        "The read-only Foundry check did not complete. The validated local bundle remains active.",
    };
  }
}

function isPalantirHostedLocation(location: BrowserLocation) {
  return location.hostname === hostedApplicationHostname;
}

async function probeAnalysisRuns(config: PalantirProbeConfig) {
  const [{ createClient }, { createPublicOauthClient }] = await Promise.all([
    import("@osdk/client"),
    import("@osdk/oauth"),
  ]);
  const auth = createPublicOauthClient(
    config.clientId,
    config.foundryUrl,
    config.redirectUrl,
    {
      useHistory: true,
      postLoginPage: config.postLoginPage,
      scopes: [...config.scopes],
    },
  );
  const client = createClient(config.foundryUrl, config.ontologyRid, auth);
  const page = await client(EchoAtlasAnalysisRun).fetchPage({ $pageSize: 1 });
  return page.data.length;
}
