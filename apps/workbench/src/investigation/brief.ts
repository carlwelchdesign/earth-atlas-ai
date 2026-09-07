import {
  dispositionLabel,
  type AssessmentEvent,
} from "../workbench/assessment";
import type { InvestigationCase } from "./model";

export const INVESTIGATION_BRIEF_VERSION = "1.0.0" as const;

export interface InvestigationBrief {
  briefVersion: typeof INVESTIGATION_BRIEF_VERSION;
  caseId: string;
  caseVersion: string;
  title: string;
  location: string;
  question: string;
  event: InvestigationCase["event"];
  acquisitions: Array<{
    role: "before" | "after";
    itemId: string;
    productId: string;
    acquiredAt: string;
    thumbnail: string;
    sourceUrl: string;
  }>;
  observations: Array<{
    id: string;
    title: string;
    sourceStatement: string;
    evidenceReference: string;
    citationId: string;
    sourceLimitations: string[];
    assessment: BriefAssessment | null;
    assessmentHistory: BriefAssessment[];
  }>;
  unresolvedObservationIds: string[];
  citations: InvestigationCase["citations"];
  attribution: string[];
  quality: InvestigationCase["quality"];
  preparedAt: string;
}

interface BriefAssessment {
  disposition: AssessmentEvent["disposition"];
  label: string;
  note: string;
  eventId: string;
  createdAt: string;
  supersedesEventId?: string;
}

function briefAssessment(event: AssessmentEvent): BriefAssessment {
  return {
    disposition: event.disposition,
    label: dispositionLabel(event.disposition),
    note: event.note,
    eventId: event.eventId,
    createdAt: event.createdAt,
    ...(event.supersedesEventId
      ? { supersedesEventId: event.supersedesEventId }
      : {}),
  };
}

export function createInvestigationBrief(
  investigation: InvestigationCase,
  events: AssessmentEvent[],
): InvestigationBrief {
  const eventsByObservation = new Map<string, AssessmentEvent[]>();
  for (const event of events) {
    const history = eventsByObservation.get(event.candidateId) ?? [];
    history.push(event);
    eventsByObservation.set(event.candidateId, history);
  }

  const observations = investigation.observations.map((observation) => {
    const history = eventsByObservation.get(observation.id) ?? [];
    const latest = history.at(-1);
    return {
      id: observation.id,
      title: observation.title,
      sourceStatement: observation.statement,
      evidenceReference: observation.evidenceReference,
      citationId: observation.citationId,
      sourceLimitations: observation.limitations,
      assessment: latest ? briefAssessment(latest) : null,
      assessmentHistory: history.map(briefAssessment),
    };
  });

  return {
    briefVersion: INVESTIGATION_BRIEF_VERSION,
    caseId: investigation.caseId,
    caseVersion: investigation.caseVersion,
    title: investigation.title,
    location: investigation.location,
    question: investigation.question,
    event: investigation.event,
    acquisitions: investigation.acquisitions.map((acquisition) => ({
      role: acquisition.role,
      itemId: acquisition.itemId,
      productId: acquisition.productId,
      acquiredAt: acquisition.acquiredAt,
      thumbnail: acquisition.thumbnail,
      sourceUrl: acquisition.sourceUrl,
    })),
    observations,
    unresolvedObservationIds: observations
      .filter((observation) => observation.assessment === null)
      .map((observation) => observation.id),
    citations: investigation.citations,
    attribution: investigation.attribution,
    quality: investigation.quality,
    preparedAt: investigation.preparedAt,
  };
}

export function createInvestigationBriefJson(
  brief: InvestigationBrief,
): string {
  return `${JSON.stringify(brief, null, 2)}\n`;
}

function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function absoluteAsset(path: string, assetOrigin: string): string {
  const origin = new URL(assetOrigin);
  const isLoopback = new Set(["localhost", "127.0.0.1", "::1"]).has(
    origin.hostname,
  );
  if (origin.protocol !== "https:" && !isLoopback) {
    throw new TypeError("Printable brief assets require an HTTPS origin.");
  }
  return new URL(path, `${origin.origin}/`).href;
}

export function createPrintableInvestigationHtml(
  brief: InvestigationBrief,
  assetOrigin: string,
): string {
  const acquisitions = brief.acquisitions
    .map(
      (acquisition) => `<figure>
        <img src="${escapeHtml(absoluteAsset(acquisition.thumbnail, assetOrigin))}" alt="${escapeHtml(acquisition.role)} satellite view of the prepared case area">
        <figcaption><strong>${escapeHtml(acquisition.role.toUpperCase())}</strong><br>${escapeHtml(acquisition.acquiredAt)}<br>${escapeHtml(acquisition.itemId)}</figcaption>
      </figure>`,
    )
    .join("");
  const observations = brief.observations
    .map(
      (observation) => `<article>
        <h3>${escapeHtml(observation.title)}</h3>
        <p><strong>Source observation:</strong> ${escapeHtml(observation.sourceStatement)}</p>
        <p><strong>Evidence reference:</strong> ${escapeHtml(observation.evidenceReference)} · citation ${escapeHtml(observation.citationId)}</p>
        <p><strong>User assessment:</strong> ${escapeHtml(observation.assessment?.label ?? "Unresolved")}</p>
        ${observation.assessment?.note ? `<p><strong>Notes:</strong> ${escapeHtml(observation.assessment.note)}</p>` : ""}
        ${observation.assessmentHistory.length > 1 ? `<p class="history">Assessment history retained: ${observation.assessmentHistory.length} events.</p>` : ""}
      </article>`,
    )
    .join("");
  const citations = brief.citations
    .map(
      (citation) =>
        `<li><a href="${escapeHtml(citation.url)}">${escapeHtml(citation.publisher)} — ${escapeHtml(citation.title)}</a> (accessed ${escapeHtml(citation.accessedAt)})</li>`,
    )
    .join("");
  const quality = [brief.quality.summary, ...brief.quality.limitations]
    .map((limitation) => `<li>${escapeHtml(limitation)}</li>`)
    .join("");
  const attribution = brief.attribution
    .map((entry) => `<li>${escapeHtml(entry)}</li>`)
    .join("");

  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>${escapeHtml(brief.title)} — investigation brief</title>
  <style>
    :root { color-scheme: light; font-family: Inter, ui-sans-serif, system-ui, sans-serif; color: #10242a; }
    body { margin: 0 auto; max-width: 940px; padding: 42px; line-height: 1.5; }
    header { border-bottom: 3px solid #117c72; margin-bottom: 28px; padding-bottom: 20px; }
    .eyebrow { color: #117c72; font-size: 12px; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; }
    h1 { font-size: 34px; margin: 5px 0; } h2 { margin-top: 32px; } h3 { margin-bottom: 6px; }
    .imagery { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
    figure { margin: 0; } img { display: block; width: 100%; } figcaption { background: #edf5f2; padding: 10px; }
    article { border-top: 1px solid #b8c8c8; padding: 12px 0; break-inside: avoid; }
    article p { margin: 6px 0; } .history { color: #53676d; font-size: 13px; }
    footer { border-top: 1px solid #b8c8c8; margin-top: 32px; padding-top: 16px; font-size: 12px; }
    @media print { body { padding: 0; } a { color: inherit; } }
  </style>
</head>
<body>
  <header>
    <p class="eyebrow">EchoAtlas prepared investigation · case ${escapeHtml(brief.caseId)} v${escapeHtml(brief.caseVersion)}</p>
    <h1>${escapeHtml(brief.title)}</h1>
    <p><strong>Investigation question:</strong> ${escapeHtml(brief.question)}</p>
    <p>${escapeHtml(brief.location)} · Event: ${escapeHtml(brief.event.occurredAt)} · Prepared: ${escapeHtml(brief.preparedAt)}</p>
  </header>
  <main>
    <section><h2>Before and after</h2><div class="imagery">${acquisitions}</div></section>
    <section><h2>Review record</h2>${observations}</section>
    <section><h2>Unresolved issues</h2><p>${brief.unresolvedObservationIds.length ? escapeHtml(brief.unresolvedObservationIds.join(", ")) : "None."}</p></section>
    <section><h2>Quality and interpretation limits</h2><ul>${quality}</ul></section>
    <section><h2>Sources</h2><ol>${citations}</ol></section>
    <section><h2>Attribution</h2><ul>${attribution}</ul></section>
  </main>
  <footer>Brief contract ${INVESTIGATION_BRIEF_VERSION}. Generated deterministically from the prepared case and browser-local assessment record. No model generated this brief.</footer>
</body>
</html>`;
}

export function downloadText(
  filename: string,
  text: string,
  mediaType: string,
): void {
  const url = URL.createObjectURL(new Blob([text], { type: mediaType }));
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}
