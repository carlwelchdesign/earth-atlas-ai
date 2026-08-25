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
}

export class AssessmentValidationError extends Error {
  constructor(message: string) {
    super(message);
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
  }: {
    candidateIds: Iterable<string>;
    now?: () => string;
  }) {
    this.#validCandidateIds = new Set(candidateIds);
    this.#now = now;
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
