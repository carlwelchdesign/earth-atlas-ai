import {
  InMemoryAssessmentStore,
  type AssessmentDraft,
  type AssessmentEvent,
} from "../workbench/assessment";

const PREFIX = "echoatlas.investigations.v1";

export class CaseAssessmentStore {
  readonly bundleId: string;
  readonly storageKey: string;
  #memory: InMemoryAssessmentStore;
  #storage: Storage | null;
  #persistenceAvailable: boolean;

  constructor({
    caseId,
    caseVersion,
    observationIds,
    storage,
  }: {
    caseId: string;
    caseVersion: string;
    observationIds: Iterable<string>;
    storage?: Storage | null;
  }) {
    this.bundleId = `${caseId}@${caseVersion}`;
    this.storageKey = `${PREFIX}.${caseId}.${caseVersion}`;
    const ids = [...observationIds];
    let selectedStorage: Storage | null = storage ?? null;
    if (storage === undefined) {
      try {
        selectedStorage = window.localStorage;
      } catch {
        selectedStorage = null;
      }
    }
    let initialEvents: AssessmentEvent[] = [];
    this.#persistenceAvailable = selectedStorage !== null;
    if (selectedStorage) {
      try {
        const serialized = selectedStorage.getItem(this.storageKey);
        if (serialized) {
          const parsed: unknown = JSON.parse(serialized);
          if (!Array.isArray(parsed) || parsed.length > 1_000) {
            throw new TypeError(
              "Stored case assessments must be a bounded list.",
            );
          }
          initialEvents = parsed as AssessmentEvent[];
        }
      } catch {
        selectedStorage = null;
        this.#persistenceAvailable = false;
        initialEvents = [];
      }
    }
    try {
      this.#memory = new InMemoryAssessmentStore({
        candidateIds: ids,
        initialEvents,
      });
    } catch {
      this.#memory = new InMemoryAssessmentStore({ candidateIds: ids });
      selectedStorage = null;
      this.#persistenceAvailable = false;
    }
    this.#storage = selectedStorage;
  }

  get persistenceAvailable(): boolean {
    return this.#persistenceAvailable;
  }

  load(): Promise<AssessmentEvent[]> {
    return this.#memory.load(this.bundleId);
  }

  async append(
    source: Omit<AssessmentDraft, "bundleId">,
  ): Promise<AssessmentEvent> {
    const event = await this.#memory.append({
      ...source,
      bundleId: this.bundleId,
    });
    if (this.#storage) {
      try {
        this.#storage.setItem(
          this.storageKey,
          JSON.stringify(await this.load()),
        );
      } catch {
        this.#storage = null;
        this.#persistenceAvailable = false;
      }
    }
    return event;
  }
}

export function latestAssessments(
  events: AssessmentEvent[],
): Map<string, AssessmentEvent> {
  const latest = new Map<string, AssessmentEvent>();
  for (const event of events) latest.set(event.candidateId, event);
  return latest;
}
