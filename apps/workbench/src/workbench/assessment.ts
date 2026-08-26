export const ASSESSMENT_DISPOSITIONS = [
  "supported",
  "rejected",
  "needs-context",
] as const;

export type AssessmentDisposition = (typeof ASSESSMENT_DISPOSITIONS)[number];

export interface AssessmentDraft {
  requestId: string;
  bundleId: string;
  candidateId: string;
  disposition: AssessmentDisposition;
  note: string;
  supersedesEventId?: string;
}

export interface AssessmentEvent extends AssessmentDraft {
  eventId: string;
  createdAt: string;
}

export interface AssessmentStore {
  append(draft: AssessmentDraft): Promise<AssessmentEvent>;
  load?(bundleId: string): Promise<AssessmentEvent[]>;
}

export class AssessmentValidationError extends Error {
  constructor(message: string, options?: ErrorOptions) {
    super(message, options);
    this.name = "AssessmentValidationError";
  }
}

export class AssessmentConflictError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "AssessmentConflictError";
  }
}

export function validateAssessmentDraft(
  draft: AssessmentDraft,
): AssessmentDraft {
  const requestId = requireText(draft.requestId, "Request ID");
  const bundleId = requireText(draft.bundleId, "Bundle ID");
  const candidateId = requireText(draft.candidateId, "Candidate ID");
  if (!ASSESSMENT_DISPOSITIONS.includes(draft.disposition)) {
    throw new AssessmentValidationError("Choose a valid assessment action.");
  }
  const note = draft.note.trim();
  if (note.length > 500) {
    throw new AssessmentValidationError(
      "Notes must be 500 characters or fewer.",
    );
  }
  if (draft.disposition === "needs-context" && note.length === 0) {
    throw new AssessmentValidationError(
      "Add a note describing the context needed.",
    );
  }
  const supersedesEventId = draft.supersedesEventId?.trim();
  if (draft.supersedesEventId !== undefined && !supersedesEventId) {
    throw new AssessmentValidationError(
      "Superseded event ID must not be empty.",
    );
  }
  return {
    requestId,
    bundleId,
    candidateId,
    disposition: draft.disposition,
    note,
    ...(supersedesEventId ? { supersedesEventId } : {}),
  };
}

export class InMemoryAssessmentStore implements AssessmentStore {
  readonly #validCandidateIds: Set<string>;
  readonly #events: AssessmentEvent[] = [];
  readonly #eventsByRequestId = new Map<string, AssessmentEvent>();
  readonly #now: () => string;
  #sequence = 0;

  constructor({
    candidateIds,
    now = () => new Date().toISOString(),
    initialEvents = [],
  }: {
    candidateIds: Iterable<string>;
    now?: () => string;
    initialEvents?: Iterable<AssessmentEvent>;
  }) {
    this.#validCandidateIds = new Set(candidateIds);
    this.#now = now;
    for (const event of initialEvents) this.#hydrate(event);
  }

  load(bundleId: string): Promise<AssessmentEvent[]> {
    return Promise.resolve(
      this.#events.filter((event) => event.bundleId === bundleId),
    );
  }

  append(source: AssessmentDraft): Promise<AssessmentEvent> {
    return Promise.resolve().then(() => this.#append(source));
  }

  #append(source: AssessmentDraft): AssessmentEvent {
    const draft = validateAssessmentDraft(source);
    const idempotentEvent = this.#eventsByRequestId.get(draft.requestId);
    if (idempotentEvent) return idempotentEvent;
    if (!this.#validCandidateIds.has(draft.candidateId)) {
      throw new AssessmentValidationError(
        `Candidate ${draft.candidateId} is not part of this bundle.`,
      );
    }
    const currentEvent = this.#findCurrentEvent(draft.candidateId);
    if (currentEvent && draft.supersedesEventId !== currentEvent.eventId) {
      throw new AssessmentConflictError(
        "This candidate already has an assessment. Start a correction from its current event.",
      );
    }
    if (!currentEvent && draft.supersedesEventId) {
      throw new AssessmentConflictError(
        "The assessment being corrected is no longer current.",
      );
    }
    this.#sequence += 1;
    const event: AssessmentEvent = {
      ...draft,
      eventId: `assessment-${String(this.#sequence).padStart(4, "0")}`,
      createdAt: this.#now(),
    };
    this.#events.push(event);
    this.#eventsByRequestId.set(event.requestId, event);
    return event;
  }

  #findCurrentEvent(candidateId: string): AssessmentEvent | undefined {
    for (let index = this.#events.length - 1; index >= 0; index -= 1) {
      const event = this.#events[index];
      if (event.candidateId === candidateId) return event;
    }
    return undefined;
  }

  #hydrate(source: AssessmentEvent) {
    const draft = validateAssessmentDraft(source);
    if (!/^assessment-[0-9]{4,}$/.test(source.eventId)) {
      throw new AssessmentValidationError(
        "Stored assessment event ID is invalid.",
      );
    }
    if (!Number.isFinite(Date.parse(source.createdAt))) {
      throw new AssessmentValidationError(
        "Stored assessment timestamp is invalid.",
      );
    }
    if (this.#events.some((event) => event.eventId === source.eventId)) {
      throw new AssessmentValidationError(
        "Stored assessment event IDs must be unique.",
      );
    }
    if (this.#eventsByRequestId.has(draft.requestId)) {
      throw new AssessmentValidationError(
        "Stored assessment request IDs must be unique.",
      );
    }
    if (!this.#validCandidateIds.has(draft.candidateId)) {
      throw new AssessmentValidationError(
        `Candidate ${draft.candidateId} is not part of this bundle.`,
      );
    }
    const current = this.#findCurrentEvent(draft.candidateId);
    if (current && draft.supersedesEventId !== current.eventId) {
      throw new AssessmentValidationError(
        "Stored assessment correction does not supersede the current event.",
      );
    }
    if (!current && draft.supersedesEventId) {
      throw new AssessmentValidationError(
        "Stored assessment correction has no prior event.",
      );
    }
    const event = {
      ...draft,
      eventId: source.eventId,
      createdAt: new Date(source.createdAt).toISOString(),
    };
    this.#events.push(event);
    this.#eventsByRequestId.set(event.requestId, event);
    this.#sequence = Math.max(
      this.#sequence,
      Number.parseInt(event.eventId.slice("assessment-".length), 10),
    );
  }
}

const LOCAL_STORAGE_PREFIX = "echoatlas.assessments.v1";
const MAX_STORED_ASSESSMENT_BYTES = 512_000;
const MAX_STORED_ASSESSMENTS = 1_000;

export class BrowserAssessmentStore implements AssessmentStore {
  readonly #candidateIds: string[];
  readonly #storage: Storage;
  readonly #stores = new Map<string, InMemoryAssessmentStore>();

  constructor({
    candidateIds,
    storage = window.localStorage,
  }: {
    candidateIds: Iterable<string>;
    storage?: Storage;
  }) {
    this.#candidateIds = [...candidateIds];
    this.#storage = storage;
  }

  async load(bundleId: string): Promise<AssessmentEvent[]> {
    return this.#getStore(bundleId).load(bundleId);
  }

  async append(draft: AssessmentDraft): Promise<AssessmentEvent> {
    const bundleId = draft.bundleId.trim();
    const current = this.#getStore(bundleId);
    const existingEvents = await current.load(bundleId);
    const next = new InMemoryAssessmentStore({
      candidateIds: this.#candidateIds,
      initialEvents: existingEvents,
    });
    const event = await next.append(draft);
    const events = await next.load(bundleId);
    if (events.length > MAX_STORED_ASSESSMENTS) {
      throw new AssessmentValidationError(
        "Local assessment history reached its 1,000-event limit.",
      );
    }
    const serialized = JSON.stringify(events);
    if (
      new TextEncoder().encode(serialized).byteLength >
      MAX_STORED_ASSESSMENT_BYTES
    ) {
      throw new AssessmentValidationError(
        "Local assessment history reached its storage-size limit.",
      );
    }
    this.#storage.setItem(this.#key(bundleId), serialized);
    this.#stores.set(bundleId, next);
    return event;
  }

  #getStore(bundleId: string): InMemoryAssessmentStore {
    const normalized = bundleId.trim();
    if (!normalized) {
      throw new AssessmentValidationError("Bundle ID must not be empty.");
    }
    const existing = this.#stores.get(normalized);
    if (existing) return existing;
    const stored = this.#storage.getItem(this.#key(normalized));
    if (
      stored &&
      new TextEncoder().encode(stored).byteLength > MAX_STORED_ASSESSMENT_BYTES
    ) {
      throw new AssessmentValidationError(
        "Stored assessment history exceeds the size limit.",
      );
    }
    let initialEvents: AssessmentEvent[] = [];
    if (stored) {
      try {
        const parsed: unknown = JSON.parse(stored);
        if (!Array.isArray(parsed) || parsed.length > MAX_STORED_ASSESSMENTS) {
          throw new TypeError("assessment history must be a bounded array");
        }
        initialEvents = parsed.map(parseStoredAssessmentEvent);
        if (initialEvents.some((event) => event.bundleId !== normalized)) {
          throw new TypeError(
            "stored assessment history contains a different bundle ID",
          );
        }
      } catch (error) {
        throw new AssessmentValidationError(
          "Stored assessment history is invalid and was not loaded.",
          { cause: error },
        );
      }
    }
    const created = new InMemoryAssessmentStore({
      candidateIds: this.#candidateIds,
      initialEvents,
    });
    this.#stores.set(normalized, created);
    return created;
  }

  #key(bundleId: string) {
    return `${LOCAL_STORAGE_PREFIX}.${bundleId}`;
  }
}

function parseStoredAssessmentEvent(source: unknown): AssessmentEvent {
  if (typeof source !== "object" || source === null) {
    throw new TypeError("stored assessment event must be an object");
  }
  const value = source as Record<string, unknown>;
  const required = [
    "requestId",
    "bundleId",
    "candidateId",
    "disposition",
    "note",
    "eventId",
    "createdAt",
  ] as const;
  for (const field of required) {
    if (typeof value[field] !== "string") {
      throw new TypeError(`stored assessment ${field} must be text`);
    }
  }
  if (
    value.supersedesEventId !== undefined &&
    typeof value.supersedesEventId !== "string"
  ) {
    throw new TypeError("stored assessment supersedesEventId must be text");
  }
  return {
    requestId: value.requestId as string,
    bundleId: value.bundleId as string,
    candidateId: value.candidateId as string,
    disposition: value.disposition as AssessmentDisposition,
    note: value.note as string,
    eventId: value.eventId as string,
    createdAt: value.createdAt as string,
    ...(typeof value.supersedesEventId === "string"
      ? { supersedesEventId: value.supersedesEventId }
      : {}),
  };
}

export function dispositionLabel(disposition: AssessmentDisposition): string {
  const labels: Record<AssessmentDisposition, string> = {
    supported: "Supported",
    rejected: "Rejected",
    "needs-context": "Needs context",
  };
  return labels[disposition];
}

function requireText(value: string, label: string): string {
  const normalized = value.trim();
  if (!normalized)
    throw new AssessmentValidationError(`${label} must not be empty.`);
  return normalized;
}
