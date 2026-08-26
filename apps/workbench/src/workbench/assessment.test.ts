import { describe, expect, it } from "vitest";

import {
  AssessmentConflictError,
  AssessmentValidationError,
  BrowserAssessmentStore,
  InMemoryAssessmentStore,
  validateAssessmentDraft,
  type AssessmentDraft,
} from "./assessment";

const draft = (overrides: Partial<AssessmentDraft> = {}): AssessmentDraft => ({
  requestId: "request-1",
  bundleId: "bundle-1",
  candidateId: "C-001",
  disposition: "supported",
  note: " Analyst reviewed the comparison. ",
  ...overrides,
});

describe("assessment domain", () => {
  it("normalizes valid drafts and requires a note for needs-context", () => {
    expect(validateAssessmentDraft(draft()).note).toBe(
      "Analyst reviewed the comparison.",
    );
    expect(() =>
      validateAssessmentDraft(
        draft({ disposition: "needs-context", note: " " }),
      ),
    ).toThrow(AssessmentValidationError);
  });

  it("returns the same event when an idempotent request is retried", async () => {
    const store = new InMemoryAssessmentStore({
      candidateIds: ["C-001"],
      now: () => "2026-08-25T00:00:00Z",
    });
    const first = await store.append(draft());
    const retry = await store.append(draft());
    expect(retry).toEqual(first);
    expect(first.eventId).toBe("assessment-0001");
  });

  it("appends a correction that references rather than replaces the prior event", async () => {
    const store = new InMemoryAssessmentStore({ candidateIds: ["C-001"] });
    const first = await store.append(draft());
    const correction = await store.append(
      draft({
        requestId: "request-2",
        disposition: "rejected",
        supersedesEventId: first.eventId,
      }),
    );
    expect(correction.eventId).not.toBe(first.eventId);
    expect(correction.supersedesEventId).toBe(first.eventId);
    expect(first).not.toHaveProperty("supersedesEventId");
  });

  it("rejects stale supersession and unknown candidates", async () => {
    const store = new InMemoryAssessmentStore({ candidateIds: ["C-001"] });
    const first = await store.append(draft());
    await store.append(
      draft({ requestId: "request-2", supersedesEventId: first.eventId }),
    );
    await expect(
      store.append(
        draft({ requestId: "request-3", supersedesEventId: first.eventId }),
      ),
    ).rejects.toThrow(AssessmentConflictError);
    await expect(
      store.append(draft({ requestId: "request-4", candidateId: "C-404" })),
    ).rejects.toThrow(AssessmentValidationError);
  });

  it("persists validated append-only events for the same bundle and origin", async () => {
    window.localStorage.clear();
    const firstStore = new BrowserAssessmentStore({
      candidateIds: ["C-001"],
    });
    const first = await firstStore.append(draft());
    const reloaded = new BrowserAssessmentStore({ candidateIds: ["C-001"] });

    expect(await reloaded.load("bundle-1")).toEqual([first]);
    const correction = await reloaded.append(
      draft({
        requestId: "request-2",
        disposition: "rejected",
        supersedesEventId: first.eventId,
      }),
    );
    expect(
      (await reloaded.load("bundle-1")).map((event) => event.eventId),
    ).toEqual([first.eventId, correction.eventId]);
  });

  it("rejects malformed or cross-bundle local assessment history", async () => {
    window.localStorage.clear();
    window.localStorage.setItem(
      "echoatlas.assessments.v1.bundle-1",
      JSON.stringify([{ eventId: "forged" }]),
    );
    await expect(
      new BrowserAssessmentStore({ candidateIds: ["C-001"] }).load("bundle-1"),
    ).rejects.toThrow(AssessmentValidationError);

    window.localStorage.setItem(
      "echoatlas.assessments.v1.bundle-1",
      JSON.stringify([
        {
          ...draft(),
          bundleId: "bundle-2",
          eventId: "assessment-0001",
          createdAt: "2026-08-25T00:00:00Z",
        },
      ]),
    );
    await expect(
      new BrowserAssessmentStore({ candidateIds: ["C-001"] }).load("bundle-1"),
    ).rejects.toThrow(AssessmentValidationError);
  });
});
