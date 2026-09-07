import { describe, expect, it } from "vitest";

import { CaseAssessmentStore, latestAssessments } from "./case-assessment";

function draft(requestId: string, supersedesEventId?: string) {
  return {
    requestId,
    candidateId: "observation-1",
    disposition: "supported" as const,
    note: "Visible in the cited imagery.",
    ...(supersedesEventId ? { supersedesEventId } : {}),
  };
}

describe("case assessment storage", () => {
  it("isolates browser history by case version", async () => {
    const first = new CaseAssessmentStore({
      caseId: "nepal",
      caseVersion: "1.0.0",
      observationIds: ["observation-1"],
      storage: window.localStorage,
    });
    await first.append(draft("request-1"));
    const reloaded = new CaseAssessmentStore({
      caseId: "nepal",
      caseVersion: "1.0.0",
      observationIds: ["observation-1"],
      storage: window.localStorage,
    });
    const nextVersion = new CaseAssessmentStore({
      caseId: "nepal",
      caseVersion: "2.0.0",
      observationIds: ["observation-1"],
      storage: window.localStorage,
    });
    expect(await reloaded.load()).toHaveLength(1);
    expect(await nextVersion.load()).toHaveLength(0);
  });

  it("retains an in-memory event when persistence fails", async () => {
    const storage = {
      getItem: () => null,
      setItem: () => {
        throw new DOMException("quota", "QuotaExceededError");
      },
    } as unknown as Storage;
    const store = new CaseAssessmentStore({
      caseId: "nepal",
      caseVersion: "1.0.0",
      observationIds: ["observation-1"],
      storage,
    });
    await store.append(draft("request-1"));
    expect(await store.load()).toHaveLength(1);
    expect(store.persistenceAvailable).toBe(false);
  });

  it("keeps corrections append-only and resolves the latest event", async () => {
    const store = new CaseAssessmentStore({
      caseId: "nepal",
      caseVersion: "1.0.0",
      observationIds: ["observation-1"],
      storage: null,
    });
    const first = await store.append(draft("request-1"));
    const second = await store.append({
      ...draft("request-2", first.eventId),
      disposition: "needs-context",
      note: "Cloud obscures the boundary.",
    });
    const events = await store.load();
    expect(events).toHaveLength(2);
    expect(second.supersedesEventId).toBe(first.eventId);
    expect(latestAssessments(events).get("observation-1")?.eventId).toBe(
      second.eventId,
    );
  });
});
