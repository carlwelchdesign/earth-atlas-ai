export const INVESTIGATION_CASE_VERSION = "1.0.0" as const;

export type Position = [number, number];

export interface PolygonGeometry {
  type: "Polygon";
  coordinates: Position[][];
}

export interface MultiPolygonGeometry {
  type: "MultiPolygon";
  coordinates: Position[][][];
}

export type CaseGeometry = PolygonGeometry | MultiPolygonGeometry;

export interface CaseCitation {
  id: string;
  publisher: string;
  title: string;
  url: string;
  accessedAt: string;
}

export interface CaseAcquisition {
  role: "before" | "after";
  itemId: string;
  productId: string;
  acquiredAt: string;
  tileTemplate: string;
  thumbnail: string;
  sourceUrl: string;
  checksumSha256: string;
  crs: string;
  resolutionMetres: number;
  cloudCoverPercent: number;
  cloudShadowPercent: number;
  nodataPercent: number;
}

export interface SourceObservation {
  id: string;
  title: string;
  statement: string;
  geometry: CaseGeometry;
  focus: Position;
  evidenceReference: string;
  citationId: string;
  limitations: string[];
}

export interface InvestigationCase {
  contractVersion: typeof INVESTIGATION_CASE_VERSION;
  caseId: string;
  caseVersion: string;
  title: string;
  location: string;
  question: string;
  event: {
    occurredAt: string;
    summary: string;
  };
  aoi: PolygonGeometry;
  coverage: PolygonGeometry;
  acquisitions: [CaseAcquisition, CaseAcquisition];
  citations: CaseCitation[];
  observations: SourceObservation[];
  attribution: string[];
  quality: {
    summary: string;
    limitations: string[];
    alignmentToleranceMetres: number;
    measuredGridResidualMetres: number[];
  };
  preparedAt: string;
  preparation: {
    command: string;
    sourceManifest: string;
  };
}

export class InvalidInvestigationCaseError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "InvalidInvestigationCaseError";
  }
}

const APPROVED_EVIDENCE_HOSTS = new Set([
  "dataspace.copernicus.eu",
  "earth-search.aws.element84.com",
  "ihp-wins.unesco.org",
  "sentinel-cogs.s3.us-west-2.amazonaws.com",
  "www.esa.int",
  "www.who.int",
]);

function record(value: unknown, path: string): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new InvalidInvestigationCaseError(`${path} must be an object.`);
  }
  return value as Record<string, unknown>;
}

function text(value: unknown, path: string): string {
  if (typeof value !== "string" || value.trim() === "") {
    throw new InvalidInvestigationCaseError(
      `${path} must be a non-empty string.`,
    );
  }
  return value;
}

function number(value: unknown, path: string): number {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    throw new InvalidInvestigationCaseError(`${path} must be a finite number.`);
  }
  return value;
}

function stringList(value: unknown, path: string): string[] {
  if (!Array.isArray(value) || value.length === 0) {
    throw new InvalidInvestigationCaseError(
      `${path} must be a non-empty list.`,
    );
  }
  return value.map((entry, index) => text(entry, `${path}[${index}]`));
}

function localAsset(value: unknown, path: string): string {
  const candidate = text(value, path);
  if (
    candidate.includes("..") ||
    candidate.includes("//") ||
    !/^\/generated-nepal\/[A-Za-z0-9][A-Za-z0-9._/{}/-]*$/.test(candidate)
  ) {
    throw new InvalidInvestigationCaseError(
      `${path} is not an approved local asset path.`,
    );
  }
  return candidate;
}

function evidenceUrl(value: unknown, path: string): string {
  const candidate = text(value, path);
  let parsed: URL;
  try {
    parsed = new URL(candidate);
  } catch {
    throw new InvalidInvestigationCaseError(`${path} must be an absolute URL.`);
  }
  if (
    parsed.protocol !== "https:" ||
    !APPROVED_EVIDENCE_HOSTS.has(parsed.hostname)
  ) {
    throw new InvalidInvestigationCaseError(
      `${path} uses an unapproved evidence host.`,
    );
  }
  return candidate;
}

function position(value: unknown, path: string): Position {
  if (!Array.isArray(value) || value.length !== 2) {
    throw new InvalidInvestigationCaseError(
      `${path} must be a longitude/latitude pair.`,
    );
  }
  const longitude = number(value[0], `${path}[0]`);
  const latitude = number(value[1], `${path}[1]`);
  if (longitude < -180 || longitude > 180 || latitude < -90 || latitude > 90) {
    throw new InvalidInvestigationCaseError(
      `${path} is outside WGS 84 bounds.`,
    );
  }
  return [longitude, latitude];
}

function ring(value: unknown, path: string): Position[] {
  if (!Array.isArray(value) || value.length < 4) {
    throw new InvalidInvestigationCaseError(
      `${path} must contain at least four positions.`,
    );
  }
  const parsed = value.map((entry, index) =>
    position(entry, `${path}[${index}]`),
  );
  if (
    parsed[0][0] !== parsed.at(-1)?.[0] ||
    parsed[0][1] !== parsed.at(-1)?.[1]
  ) {
    throw new InvalidInvestigationCaseError(`${path} must be closed.`);
  }
  return parsed;
}

function geometry(value: unknown, path: string): CaseGeometry {
  const source = record(value, path);
  if (source.type === "Polygon") {
    if (!Array.isArray(source.coordinates) || source.coordinates.length === 0) {
      throw new InvalidInvestigationCaseError(
        `${path}.coordinates must contain rings.`,
      );
    }
    return {
      type: "Polygon",
      coordinates: source.coordinates.map((entry, index) =>
        ring(entry, `${path}.coordinates[${index}]`),
      ),
    };
  }
  if (source.type === "MultiPolygon") {
    if (!Array.isArray(source.coordinates) || source.coordinates.length === 0) {
      throw new InvalidInvestigationCaseError(
        `${path}.coordinates must contain polygons.`,
      );
    }
    return {
      type: "MultiPolygon",
      coordinates: source.coordinates.map((polygon, polygonIndex) => {
        if (!Array.isArray(polygon) || polygon.length === 0) {
          throw new InvalidInvestigationCaseError(
            `${path}.coordinates[${polygonIndex}] is empty.`,
          );
        }
        return polygon.map((entry, ringIndex) =>
          ring(entry, `${path}.coordinates[${polygonIndex}][${ringIndex}]`),
        );
      }),
    };
  }
  throw new InvalidInvestigationCaseError(
    `${path}.type must be Polygon or MultiPolygon.`,
  );
}

function polygon(value: unknown, path: string): PolygonGeometry {
  const parsed = geometry(value, path);
  if (parsed.type !== "Polygon") {
    throw new InvalidInvestigationCaseError(`${path} must be a Polygon.`);
  }
  return parsed;
}

function parseCitation(value: unknown, index: number): CaseCitation {
  const path = `citations[${index}]`;
  const source = record(value, path);
  return {
    id: text(source.id, `${path}.id`),
    publisher: text(source.publisher, `${path}.publisher`),
    title: text(source.title, `${path}.title`),
    url: evidenceUrl(source.url, `${path}.url`),
    accessedAt: text(source.accessedAt, `${path}.accessedAt`),
  };
}

function parseAcquisition(value: unknown, index: number): CaseAcquisition {
  const path = `acquisitions[${index}]`;
  const source = record(value, path);
  if (source.role !== "before" && source.role !== "after") {
    throw new InvalidInvestigationCaseError(
      `${path}.role must be before or after.`,
    );
  }
  const checksumSha256 = text(source.checksumSha256, `${path}.checksumSha256`);
  if (!/^[a-f0-9]{64}$/.test(checksumSha256)) {
    throw new InvalidInvestigationCaseError(
      `${path}.checksumSha256 must be SHA-256.`,
    );
  }
  return {
    role: source.role,
    itemId: text(source.itemId, `${path}.itemId`),
    productId: text(source.productId, `${path}.productId`),
    acquiredAt: text(source.acquiredAt, `${path}.acquiredAt`),
    tileTemplate: localAsset(source.tileTemplate, `${path}.tileTemplate`),
    thumbnail: localAsset(source.thumbnail, `${path}.thumbnail`),
    sourceUrl: evidenceUrl(source.sourceUrl, `${path}.sourceUrl`),
    checksumSha256,
    crs: text(source.crs, `${path}.crs`),
    resolutionMetres: number(
      source.resolutionMetres,
      `${path}.resolutionMetres`,
    ),
    cloudCoverPercent: number(
      source.cloudCoverPercent,
      `${path}.cloudCoverPercent`,
    ),
    cloudShadowPercent: number(
      source.cloudShadowPercent,
      `${path}.cloudShadowPercent`,
    ),
    nodataPercent: number(source.nodataPercent, `${path}.nodataPercent`),
  };
}

export function parseInvestigationCase(value: unknown): InvestigationCase {
  const source = record(value, "case");
  if (source.contractVersion !== INVESTIGATION_CASE_VERSION) {
    throw new InvalidInvestigationCaseError(
      `case.contractVersion must be ${INVESTIGATION_CASE_VERSION}.`,
    );
  }
  if (!Array.isArray(source.acquisitions) || source.acquisitions.length !== 2) {
    throw new InvalidInvestigationCaseError(
      "acquisitions must contain before and after records.",
    );
  }
  const acquisitions = source.acquisitions.map(parseAcquisition) as [
    CaseAcquisition,
    CaseAcquisition,
  ];
  if (acquisitions[0].role !== "before" || acquisitions[1].role !== "after") {
    throw new InvalidInvestigationCaseError(
      "acquisitions must be ordered before, then after.",
    );
  }
  if (!Array.isArray(source.citations) || source.citations.length === 0) {
    throw new InvalidInvestigationCaseError(
      "citations must be a non-empty list.",
    );
  }
  const citations = source.citations.map(parseCitation);
  const citationIds = new Set(citations.map((citation) => citation.id));
  if (citationIds.size !== citations.length) {
    throw new InvalidInvestigationCaseError("citation IDs must be unique.");
  }
  if (!Array.isArray(source.observations) || source.observations.length === 0) {
    throw new InvalidInvestigationCaseError(
      "observations must be a non-empty list.",
    );
  }
  const observations = source.observations.map(
    (entry, index): SourceObservation => {
      const path = `observations[${index}]`;
      const observation = record(entry, path);
      const citationId = text(observation.citationId, `${path}.citationId`);
      if (!citationIds.has(citationId)) {
        throw new InvalidInvestigationCaseError(
          `${path}.citationId is not declared.`,
        );
      }
      return {
        id: text(observation.id, `${path}.id`),
        title: text(observation.title, `${path}.title`),
        statement: text(observation.statement, `${path}.statement`),
        geometry: geometry(observation.geometry, `${path}.geometry`),
        focus: position(observation.focus, `${path}.focus`),
        evidenceReference: text(
          observation.evidenceReference,
          `${path}.evidenceReference`,
        ),
        citationId,
        limitations: stringList(observation.limitations, `${path}.limitations`),
      };
    },
  );
  if (
    new Set(observations.map((observation) => observation.id)).size !==
    observations.length
  ) {
    throw new InvalidInvestigationCaseError("observation IDs must be unique.");
  }
  const event = record(source.event, "event");
  const quality = record(source.quality, "quality");
  const preparation = record(source.preparation, "preparation");
  if (
    !Array.isArray(quality.measuredGridResidualMetres) ||
    quality.measuredGridResidualMetres.length !== 5
  ) {
    throw new InvalidInvestigationCaseError(
      "quality.measuredGridResidualMetres must contain five controls.",
    );
  }
  return {
    contractVersion: INVESTIGATION_CASE_VERSION,
    caseId: text(source.caseId, "caseId"),
    caseVersion: text(source.caseVersion, "caseVersion"),
    title: text(source.title, "title"),
    location: text(source.location, "location"),
    question: text(source.question, "question"),
    event: {
      occurredAt: text(event.occurredAt, "event.occurredAt"),
      summary: text(event.summary, "event.summary"),
    },
    aoi: polygon(source.aoi, "aoi"),
    coverage: polygon(source.coverage, "coverage"),
    acquisitions,
    citations,
    observations,
    attribution: stringList(source.attribution, "attribution"),
    quality: {
      summary: text(quality.summary, "quality.summary"),
      limitations: stringList(quality.limitations, "quality.limitations"),
      alignmentToleranceMetres: number(
        quality.alignmentToleranceMetres,
        "quality.alignmentToleranceMetres",
      ),
      measuredGridResidualMetres: quality.measuredGridResidualMetres.map(
        (entry, index) =>
          number(entry, `quality.measuredGridResidualMetres[${index}]`),
      ),
    },
    preparedAt: text(source.preparedAt, "preparedAt"),
    preparation: {
      command: text(preparation.command, "preparation.command"),
      sourceManifest: localAsset(
        preparation.sourceManifest,
        "preparation.sourceManifest",
      ),
    },
  };
}

export async function loadInvestigationCase(): Promise<InvestigationCase> {
  const response = await fetch("/generated-nepal/case.json", {
    cache: "no-store",
  });
  if (!response.ok)
    throw new Error(`Case source returned HTTP ${response.status}.`);
  return parseInvestigationCase(await response.json());
}
