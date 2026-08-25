export const WORKBENCH_CONTRACT_VERSION = "1.0.0" as const;

export type AcquisitionRole = "before" | "after";
export type BundleStatus = "succeeded" | "partial";
export type ComparisonMode = "before" | "two-up" | "after";

export interface AcquisitionView {
  id: string;
  role: AcquisitionRole;
  acquiredAt: string;
  label: string;
  artifact: {
    available: boolean;
    mediaType: "image/svg+xml";
    src: string;
  };
}

export interface CandidateView {
  id: string;
  areaSquareMeters: number;
  pixelCount: number;
  heuristicScore: number;
  warningCount: number;
  mapPosition: {
    leftPercent: number;
    topPercent: number;
    widthPercent: number;
    heightPercent: number;
    rotationDegrees: number;
  };
}

export interface WorkbenchBundle {
  contractVersion: typeof WORKBENCH_CONTRACT_VERSION;
  bundleId: string;
  status: BundleStatus;
  createdAt: string;
  mission: {
    title: string;
    boundaryLabel: string;
  };
  acquisitions: [AcquisitionView, AcquisitionView];
  candidates: CandidateView[];
  qualityWarnings: string[];
}

export type BundleLoader = () => Promise<unknown>;

export class InvalidWorkbenchBundleError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "InvalidWorkbenchBundleError";
  }
}

export function parseWorkbenchBundle(source: unknown): WorkbenchBundle {
  const root = requireRecord(source, "bundle");
  requireExact(
    root.contractVersion,
    WORKBENCH_CONTRACT_VERSION,
    "contractVersion",
  );
  const bundleId = requireString(root.bundleId, "bundleId");
  const status = requireEnum(root.status, ["succeeded", "partial"], "status");
  const createdAt = requireTimestamp(root.createdAt, "createdAt");
  const missionSource = requireRecord(root.mission, "mission");
  const mission = {
    title: requireString(missionSource.title, "mission.title"),
    boundaryLabel: requireString(
      missionSource.boundaryLabel,
      "mission.boundaryLabel",
    ),
  };
  const acquisitionSources = requireArray(root.acquisitions, "acquisitions");
  if (acquisitionSources.length !== 2) {
    throw invalid("acquisitions must contain exactly before and after records");
  }
  const parsedAcquisitions = acquisitionSources.map(parseAcquisition);
  const roles = new Set(
    parsedAcquisitions.map((acquisition) => acquisition.role),
  );
  if (!roles.has("before") || !roles.has("after")) {
    throw invalid("acquisitions must contain exactly before and after roles");
  }
  const before = parsedAcquisitions.find(
    (acquisition) => acquisition.role === "before",
  );
  const after = parsedAcquisitions.find(
    (acquisition) => acquisition.role === "after",
  );
  if (!before || !after) {
    throw invalid("acquisitions must contain exactly before and after roles");
  }
  const candidates = requireArray(root.candidates, "candidates").map(
    parseCandidate,
  );
  const candidateIds = new Set<string>();
  for (const candidate of candidates) {
    if (candidateIds.has(candidate.id))
      throw invalid(`duplicate candidate ID: ${candidate.id}`);
    candidateIds.add(candidate.id);
  }
  const qualityWarnings = requireArray(
    root.qualityWarnings,
    "qualityWarnings",
  ).map((warning, index) =>
    requireString(warning, `qualityWarnings[${index}]`),
  );
  return {
    contractVersion: WORKBENCH_CONTRACT_VERSION,
    bundleId,
    status,
    createdAt,
    mission,
    acquisitions: [before, after],
    candidates,
    qualityWarnings,
  };
}

function parseAcquisition(source: unknown, index: number): AcquisitionView {
  const record = requireRecord(source, `acquisitions[${index}]`);
  const artifactSource = requireRecord(
    record.artifact,
    `acquisitions[${index}].artifact`,
  );
  const role = requireEnum(
    record.role,
    ["before", "after"],
    `acquisitions[${index}].role`,
  );
  const mediaType = requireExact(
    artifactSource.mediaType,
    "image/svg+xml",
    `acquisitions[${index}].artifact.mediaType`,
  );
  const src = requireSafeFixturePath(
    artifactSource.src,
    `acquisitions[${index}].artifact.src`,
  );
  return {
    id: requireString(record.id, `acquisitions[${index}].id`),
    role,
    acquiredAt: requireTimestamp(
      record.acquiredAt,
      `acquisitions[${index}].acquiredAt`,
    ),
    label: requireString(record.label, `acquisitions[${index}].label`),
    artifact: {
      available: requireBoolean(
        artifactSource.available,
        `acquisitions[${index}].artifact.available`,
      ),
      mediaType,
      src,
    },
  };
}

function parseCandidate(source: unknown, index: number): CandidateView {
  const record = requireRecord(source, `candidates[${index}]`);
  const position = requireRecord(
    record.mapPosition,
    `candidates[${index}].mapPosition`,
  );
  return {
    id: requireString(record.id, `candidates[${index}].id`),
    areaSquareMeters: requirePositiveNumber(
      record.areaSquareMeters,
      `candidates[${index}].areaSquareMeters`,
    ),
    pixelCount: requirePositiveInteger(
      record.pixelCount,
      `candidates[${index}].pixelCount`,
    ),
    heuristicScore: requireUnitInterval(
      record.heuristicScore,
      `candidates[${index}].heuristicScore`,
    ),
    warningCount: requireNonNegativeInteger(
      record.warningCount,
      `candidates[${index}].warningCount`,
    ),
    mapPosition: {
      leftPercent: requirePercent(
        position.leftPercent,
        `candidates[${index}].leftPercent`,
      ),
      topPercent: requirePercent(
        position.topPercent,
        `candidates[${index}].topPercent`,
      ),
      widthPercent: requirePercent(
        position.widthPercent,
        `candidates[${index}].widthPercent`,
      ),
      heightPercent: requirePercent(
        position.heightPercent,
        `candidates[${index}].heightPercent`,
      ),
      rotationDegrees: requireNumber(
        position.rotationDegrees,
        `candidates[${index}].rotationDegrees`,
      ),
    },
  };
}

function requireRecord(value: unknown, path: string): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw invalid(`${path} must be an object`);
  }
  return value as Record<string, unknown>;
}

function requireArray(value: unknown, path: string): unknown[] {
  if (!Array.isArray(value)) throw invalid(`${path} must be an array`);
  return value;
}

function requireString(value: unknown, path: string): string {
  if (typeof value !== "string" || value.trim().length === 0) {
    throw invalid(`${path} must be a non-empty string`);
  }
  return value;
}

function requireBoolean(value: unknown, path: string): boolean {
  if (typeof value !== "boolean") throw invalid(`${path} must be a boolean`);
  return value;
}

function requireNumber(value: unknown, path: string): number {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    throw invalid(`${path} must be a finite number`);
  }
  return value;
}

function requirePositiveNumber(value: unknown, path: string): number {
  const number = requireNumber(value, path);
  if (number <= 0) throw invalid(`${path} must be positive`);
  return number;
}

function requirePositiveInteger(value: unknown, path: string): number {
  const number = requirePositiveNumber(value, path);
  if (!Number.isInteger(number)) throw invalid(`${path} must be an integer`);
  return number;
}

function requireNonNegativeInteger(value: unknown, path: string): number {
  const number = requireNumber(value, path);
  if (!Number.isInteger(number) || number < 0) {
    throw invalid(`${path} must be a non-negative integer`);
  }
  return number;
}

function requireUnitInterval(value: unknown, path: string): number {
  const number = requireNumber(value, path);
  if (number < 0 || number > 1)
    throw invalid(`${path} must be between 0 and 1`);
  return number;
}

function requirePercent(value: unknown, path: string): number {
  const number = requireNumber(value, path);
  if (number < 0 || number > 100)
    throw invalid(`${path} must be between 0 and 100`);
  return number;
}

function requireTimestamp(value: unknown, path: string): string {
  const timestamp = requireString(value, path);
  if (Number.isNaN(Date.parse(timestamp)))
    throw invalid(`${path} must be an ISO timestamp`);
  return timestamp;
}

function requireSafeFixturePath(value: unknown, path: string): string {
  const source = requireString(value, path);
  if (
    !/^\/fixtures\/[A-Za-z0-9][A-Za-z0-9._/-]*$/.test(source) ||
    source.includes("..")
  ) {
    throw invalid(`${path} must be a safe local fixture path`);
  }
  return source;
}

function requireExact<const T extends string>(
  value: unknown,
  expected: T,
  path: string,
): T {
  if (value !== expected) throw invalid(`${path} must equal ${expected}`);
  return expected;
}

function requireEnum<const T extends string>(
  value: unknown,
  allowed: readonly T[],
  path: string,
): T {
  if (typeof value !== "string" || !allowed.includes(value as T)) {
    throw invalid(`${path} must be one of ${allowed.join(", ")}`);
  }
  return value as T;
}

function invalid(message: string): InvalidWorkbenchBundleError {
  return new InvalidWorkbenchBundleError(message);
}
