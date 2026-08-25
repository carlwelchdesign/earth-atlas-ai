import type { AssessmentEvent } from "./assessment";
import type { CandidateView, WorkbenchBundle } from "./model";

export interface CandidateEvidenceExport {
  exportVersion: "1.0.0";
  exportedAt: string;
  bundle: {
    id: string;
    contractVersion: string;
    status: string;
    createdAt: string;
  };
  candidate: CandidateView;
  provenance: WorkbenchBundle["evidence"];
  assessments: AssessmentEvent[];
}

export function createCandidateEvidenceExport({
  bundle,
  candidate,
  assessments,
  exportedAt,
}: {
  bundle: WorkbenchBundle;
  candidate: CandidateView;
  assessments: AssessmentEvent[];
  exportedAt: string;
}): CandidateEvidenceExport {
  return {
    exportVersion: "1.0.0",
    exportedAt,
    bundle: {
      id: bundle.bundleId,
      contractVersion: bundle.contractVersion,
      status: bundle.status,
      createdAt: bundle.createdAt,
    },
    candidate,
    provenance: bundle.evidence,
    assessments,
  };
}

export function createEvidenceDownloadHref(record: CandidateEvidenceExport) {
  return `data:application/json;charset=utf-8,${encodeURIComponent(
    `${JSON.stringify(record, null, 2)}\n`,
  )}`;
}
