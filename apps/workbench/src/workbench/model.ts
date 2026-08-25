export const WORKBENCH_CONTRACT_VERSION = "1.0.0" as const;
const ALLOWED_EVIDENCE_HOSTS = new Set([
  "creativecommons.org",
  "umbra-open-data-catalog.s3.us-west-2.amazonaws.com",
]);

export type AcquisitionRole = "before" | "after";
export type BundleStatus = "succeeded" | "partial";
export type ComparisonMode = "before" | "two-up" | "after";
export type FreshnessState = "current" | "stale";
export type AssessmentPermissionState = "allowed" | "denied";

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
  evidenceArtifactIds: string[];
  warnings: string[];
  mapPosition: {
    leftPercent: number;
    topPercent: number;
    widthPercent: number;
    heightPercent: number;
    rotationDegrees: number;
  };
}

export type EvidenceLinkStatus = "available" | "unavailable";

export interface EvidenceLink {
  label: string;
  href: string | null;
  status: EvidenceLinkStatus;
}

export interface AcquisitionEvidence {
  acquisitionId: string;
  provider: string;
  productType: string;
  polarization: string;
  resolutionMeters: number;
  incidenceAngleDegrees: number;
  source: EvidenceLink;
  checksum: {
    algorithm: string;
    value: string;
  };
}

export interface EvidenceArtifact {
  id: string;
  label: string;
  mediaType: string;
  path: string;
  sha256: string;
  sizeBytes: number;
  required: boolean;
  available: boolean;
}

export interface EvidenceView {
  lineage: "synthetic-fixture" | "satellite-derived";
  lineageNotice: string;
  attribution: string;
  license: EvidenceLink;
  software: {
    version: string;
    commit: string;
  };
  run: {
    id: string;
    parameters: Array<{ name: string; value: string }>;
  };
  acquisitions: [AcquisitionEvidence, AcquisitionEvidence];
  artifacts: EvidenceArtifact[];
  warnings: string[];
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
  freshness: {
    state: FreshnessState;
    evaluatedAt: string;
    reason: string | null;
  };
  permissions: {
    assessments: {
      state: AssessmentPermissionState;
      reason: string | null;
    };
  };
  acquisitions: [AcquisitionView, AcquisitionView];
  candidates: CandidateView[];
  qualityWarnings: string[];
  evidence: EvidenceView;
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
  const freshnessSource = requireRecord(root.freshness, "freshness");
  const freshness = {
    state: requireEnum(
      freshnessSource.state,
      ["current", "stale"],
      "freshness.state",
    ),
    evaluatedAt: requireTimestamp(
      freshnessSource.evaluatedAt,
      "freshness.evaluatedAt",
    ),
    reason: requireNullableString(freshnessSource.reason, "freshness.reason"),
  };
  if (freshness.state === "stale" && freshness.reason === null) {
    throw invalid("freshness.reason is required when the bundle is stale");
  }
  const permissionsSource = requireRecord(root.permissions, "permissions");
  const assessmentPermissionSource = requireRecord(
    permissionsSource.assessments,
    "permissions.assessments",
  );
  const assessmentPermission = {
    state: requireEnum(
      assessmentPermissionSource.state,
      ["allowed", "denied"],
      "permissions.assessments.state",
    ),
    reason: requireNullableString(
      assessmentPermissionSource.reason,
      "permissions.assessments.reason",
    ),
  };
  if (
    assessmentPermission.state === "denied" &&
    assessmentPermission.reason === null
  ) {
    throw invalid(
      "permissions.assessments.reason is required when permission is denied",
    );
  }
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
  const evidence = parseEvidence(root.evidence);
  const acquisitionIds = new Set(
    parsedAcquisitions.map((acquisition) => acquisition.id),
  );
  const evidenceAcquisitionIds = new Set<string>();
  for (const acquisition of evidence.acquisitions) {
    if (evidenceAcquisitionIds.has(acquisition.acquisitionId)) {
      throw invalid(
        `duplicate evidence acquisition ID: ${acquisition.acquisitionId}`,
      );
    }
    evidenceAcquisitionIds.add(acquisition.acquisitionId);
    if (!acquisitionIds.has(acquisition.acquisitionId)) {
      throw invalid(
        `evidence acquisition does not reference a bundle acquisition: ${acquisition.acquisitionId}`,
      );
    }
  }
  const artifactIds = new Set(
    evidence.artifacts.map((artifact) => artifact.id),
  );
  for (const candidate of candidates) {
    for (const artifactId of candidate.evidenceArtifactIds) {
      if (!artifactIds.has(artifactId)) {
        throw invalid(
          `candidate ${candidate.id} references unknown evidence artifact: ${artifactId}`,
        );
      }
    }
  }
  return {
    contractVersion: WORKBENCH_CONTRACT_VERSION,
    bundleId,
    status,
    createdAt,
    mission,
    freshness,
    permissions: { assessments: assessmentPermission },
    acquisitions: [before, after],
    candidates,
    qualityWarnings,
    evidence,
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
    evidenceArtifactIds: requireArray(
      record.evidenceArtifactIds,
      `candidates[${index}].evidenceArtifactIds`,
    ).map((id, artifactIndex) =>
      requireString(
        id,
        `candidates[${index}].evidenceArtifactIds[${artifactIndex}]`,
      ),
    ),
    warnings: requireArray(
      record.warnings,
      `candidates[${index}].warnings`,
    ).map((warning, warningIndex) =>
      requireString(warning, `candidates[${index}].warnings[${warningIndex}]`),
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

function parseEvidence(source: unknown): EvidenceView {
  const record = requireRecord(source, "evidence");
  const license = parseEvidenceLink(record.license, "evidence.license");
  const software = requireRecord(record.software, "evidence.software");
  const run = requireRecord(record.run, "evidence.run");
  const acquisitions = requireArray(
    record.acquisitions,
    "evidence.acquisitions",
  ).map((item, index) => parseAcquisitionEvidence(item, index));
  if (acquisitions.length !== 2) {
    throw invalid("evidence.acquisitions must contain exactly two records");
  }
  const artifacts = requireArray(record.artifacts, "evidence.artifacts").map(
    (item, index) => parseEvidenceArtifact(item, index),
  );
  const artifactIds = new Set<string>();
  for (const artifact of artifacts) {
    if (artifactIds.has(artifact.id)) {
      throw invalid(`duplicate evidence artifact ID: ${artifact.id}`);
    }
    artifactIds.add(artifact.id);
  }
  return {
    lineage: requireEnum(
      record.lineage,
      ["synthetic-fixture", "satellite-derived"],
      "evidence.lineage",
    ),
    lineageNotice: requireString(
      record.lineageNotice,
      "evidence.lineageNotice",
    ),
    attribution: requireString(record.attribution, "evidence.attribution"),
    license,
    software: {
      version: requireString(software.version, "evidence.software.version"),
      commit: requireCommit(software.commit, "evidence.software.commit"),
    },
    run: {
      id: requireString(run.id, "evidence.run.id"),
      parameters: requireArray(run.parameters, "evidence.run.parameters").map(
        (item, index) => {
          const parameter = requireRecord(
            item,
            `evidence.run.parameters[${index}]`,
          );
          return {
            name: requireString(
              parameter.name,
              `evidence.run.parameters[${index}].name`,
            ),
            value: requireString(
              parameter.value,
              `evidence.run.parameters[${index}].value`,
            ),
          };
        },
      ),
    },
    acquisitions: acquisitions as [AcquisitionEvidence, AcquisitionEvidence],
    artifacts,
    warnings: requireArray(record.warnings, "evidence.warnings").map(
      (warning, index) => requireString(warning, `evidence.warnings[${index}]`),
    ),
  };
}

function parseAcquisitionEvidence(
  source: unknown,
  index: number,
): AcquisitionEvidence {
  const path = `evidence.acquisitions[${index}]`;
  const record = requireRecord(source, path);
  const checksum = requireRecord(record.checksum, `${path}.checksum`);
  return {
    acquisitionId: requireString(record.acquisitionId, `${path}.acquisitionId`),
    provider: requireString(record.provider, `${path}.provider`),
    productType: requireString(record.productType, `${path}.productType`),
    polarization: requireString(record.polarization, `${path}.polarization`),
    resolutionMeters: requirePositiveNumber(
      record.resolutionMeters,
      `${path}.resolutionMeters`,
    ),
    incidenceAngleDegrees: requirePositiveNumber(
      record.incidenceAngleDegrees,
      `${path}.incidenceAngleDegrees`,
    ),
    source: parseEvidenceLink(record.source, `${path}.source`),
    checksum: {
      algorithm: requireString(
        checksum.algorithm,
        `${path}.checksum.algorithm`,
      ),
      value: requireString(checksum.value, `${path}.checksum.value`),
    },
  };
}

function parseEvidenceLink(source: unknown, path: string): EvidenceLink {
  const record = requireRecord(source, path);
  const status = requireEnum(
    record.status,
    ["available", "unavailable"],
    `${path}.status`,
  );
  const href =
    record.href === null ? null : requireSafeLink(record.href, `${path}.href`);
  if (status === "available" && href === null) {
    throw invalid(`${path}.href is required when the link is available`);
  }
  if (status === "unavailable" && href !== null) {
    throw invalid(`${path}.href must be null when the link is unavailable`);
  }
  return {
    label: requireString(record.label, `${path}.label`),
    href,
    status,
  };
}

function parseEvidenceArtifact(
  source: unknown,
  index: number,
): EvidenceArtifact {
  const path = `evidence.artifacts[${index}]`;
  const record = requireRecord(source, path);
  const available = requireBoolean(record.available, `${path}.available`);
  const required = requireBoolean(record.required, `${path}.required`);
  if (required && !available) {
    throw invalid(`${path} cannot be required and unavailable`);
  }
  return {
    id: requireString(record.id, `${path}.id`),
    label: requireString(record.label, `${path}.label`),
    mediaType: requireMediaType(record.mediaType, `${path}.mediaType`),
    path: requireSafeFixturePath(record.path, `${path}.path`),
    sha256: requireSha256(record.sha256, `${path}.sha256`),
    sizeBytes: requirePositiveInteger(record.sizeBytes, `${path}.sizeBytes`),
    required,
    available,
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

function requireNullableString(value: unknown, path: string): string | null {
  if (value === null) return null;
  return requireString(value, path);
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

function requireSafeLink(value: unknown, path: string): string {
  const source = requireString(value, path);
  if (source.startsWith("/fixtures/"))
    return requireSafeFixturePath(source, path);
  let url: URL;
  try {
    url = new URL(source);
  } catch {
    throw invalid(`${path} must be a safe local fixture path or HTTPS URL`);
  }
  if (url.protocol !== "https:" || url.username || url.password) {
    throw invalid(`${path} must be an unauthenticated HTTPS URL`);
  }
  if (!ALLOWED_EVIDENCE_HOSTS.has(url.hostname)) {
    throw invalid(`${path} host is not allowlisted`);
  }
  return url.href;
}

function requireSha256(value: unknown, path: string): string {
  const checksum = requireString(value, path);
  if (!/^[a-f0-9]{64}$/.test(checksum)) {
    throw invalid(`${path} must be a lowercase SHA-256 checksum`);
  }
  return checksum;
}

function requireCommit(value: unknown, path: string): string {
  const commit = requireString(value, path);
  if (!/^[a-f0-9]{7,64}$/.test(commit)) {
    throw invalid(`${path} must be a Git commit identifier`);
  }
  return commit;
}

function requireMediaType(value: unknown, path: string): string {
  const mediaType = requireString(value, path);
  if (!/^[a-z0-9.+-]+\/[a-z0-9.+-]+$/.test(mediaType)) {
    throw invalid(`${path} must be a media type`);
  }
  return mediaType;
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
