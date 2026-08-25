"""Validated contracts for candidate evaluation sets and reports."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

ReviewStatus = Literal[
    "pending", "synthetic-established", "engineering-reviewed", "domain-reviewed"
]
FailureClass = Literal[
    "geometry",
    "water-moisture",
    "speckle",
    "shadow-layover",
    "registration-artifact",
    "other",
]


class EvaluationGrid(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    crs: str = Field(min_length=1)
    width: int = Field(gt=0, le=100_000)
    height: int = Field(gt=0, le=100_000)
    transform: tuple[float, float, float, float, float, float]

    @model_validator(mode="after")
    def limit_grid_allocation(self) -> EvaluationGrid:
        if self.width * self.height > 25_000_000:
            raise ValueError("evaluation grid cannot exceed 25 million pixels")
        return self


class RegionLabel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    region_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
    geometry: dict[str, object]
    review_status: ReviewStatus
    reviewer: str | None = None
    reviewed_at: datetime | None = None
    guidance_version: str = Field(min_length=1)

    @model_validator(mode="after")
    def require_reviewer_for_reviewed_label(self) -> RegionLabel:
        reviewed = self.review_status in {"engineering-reviewed", "domain-reviewed"}
        if reviewed and (self.reviewer is None or self.reviewed_at is None):
            raise ValueError("reviewed labels require reviewer and reviewed_at")
        if not reviewed and (self.reviewer is not None or self.reviewed_at is not None):
            raise ValueError("unreviewed labels cannot name a reviewer or reviewed_at")
        return self


class FalsePositiveAnnotation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    candidate_id: str = Field(min_length=1)
    failure_class: FailureClass
    review_status: ReviewStatus
    reviewer: str | None = None
    reviewed_at: datetime | None = None

    @model_validator(mode="after")
    def require_reviewer_for_reviewed_annotation(self) -> FalsePositiveAnnotation:
        reviewed = self.review_status in {"engineering-reviewed", "domain-reviewed"}
        if reviewed and (self.reviewer is None or self.reviewed_at is None):
            raise ValueError("reviewed annotations require reviewer and reviewed_at")
        if not reviewed and (self.reviewer is not None or self.reviewed_at is not None):
            raise ValueError("unreviewed annotations cannot name a reviewer or reviewed_at")
        return self


class EvaluationCase(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    case_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
    fixture_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
    prediction_path: str = Field(min_length=1)
    grid: EvaluationGrid
    geometry_crs: str = Field(min_length=1)
    evaluation_geometry: dict[str, object]
    reference_regions: tuple[RegionLabel, ...]
    false_positive_annotations: tuple[FalsePositiveAnnotation, ...] = ()
    limitations: tuple[str, ...] = ()

    @model_validator(mode="after")
    def require_unique_ids(self) -> EvaluationCase:
        region_ids = [region.region_id for region in self.reference_regions]
        annotation_ids = [item.candidate_id for item in self.false_positive_annotations]
        if len(region_ids) != len(set(region_ids)):
            raise ValueError("reference region IDs must be unique within a case")
        if len(annotation_ids) != len(set(annotation_ids)):
            raise ValueError("false-positive annotation IDs must be unique within a case")
        return self


class SourceArtifact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    artifact_id: str = Field(min_length=1)
    source_identity: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    role: str = Field(min_length=1)


class EvaluationSetProvenance(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    source_kind: Literal["synthetic", "derived-public-sar"]
    source_description: str = Field(min_length=1)
    source_license: str = Field(min_length=1)
    created_at: datetime
    labeling_guidance: str = Field(min_length=1)
    labeling_guidance_version: str = Field(min_length=1)
    source_artifacts: tuple[SourceArtifact, ...] = ()

    @model_validator(mode="after")
    def require_public_source_artifacts(self) -> EvaluationSetProvenance:
        artifact_ids = [artifact.artifact_id for artifact in self.source_artifacts]
        if len(artifact_ids) != len(set(artifact_ids)):
            raise ValueError("source artifact IDs must be unique")
        if self.source_kind == "derived-public-sar" and not self.source_artifacts:
            raise ValueError("derived public SAR provenance requires source artifacts")
        return self


class EvaluationSet(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    evaluation_set_version: Literal["1.0.0"] = "1.0.0"
    evaluation_set_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
    purpose: Literal["software-verification", "pipeline-benchmark"]
    provenance: EvaluationSetProvenance
    candidate_iou_threshold: float = Field(default=0.5, gt=0, le=1)
    tuning_fixture_ids: tuple[str, ...]
    cases: tuple[EvaluationCase, ...]
    limitations: tuple[str, ...]

    @model_validator(mode="after")
    def enforce_fixture_separation(self) -> EvaluationSet:
        case_ids = [case.case_id for case in self.cases]
        fixture_ids = [case.fixture_id for case in self.cases]
        if not self.cases:
            raise ValueError("evaluation set must contain at least one case")
        if len(case_ids) != len(set(case_ids)):
            raise ValueError("evaluation case IDs must be unique")
        if len(fixture_ids) != len(set(fixture_ids)):
            raise ValueError("evaluation fixture IDs must be unique")
        overlap = sorted(set(fixture_ids) & set(self.tuning_fixture_ids))
        if overlap:
            raise ValueError(f"evaluation fixtures overlap tuning fixtures: {', '.join(overlap)}")
        statuses = {
            *(region.review_status for case in self.cases for region in case.reference_regions),
            *(
                annotation.review_status
                for case in self.cases
                for annotation in case.false_positive_annotations
            ),
        }
        if "pending" in statuses:
            raise ValueError("pending labels cannot enter evaluation metric denominators")
        if self.purpose == "pipeline-benchmark":
            if self.provenance.source_kind != "derived-public-sar":
                raise ValueError("pipeline benchmarks require derived public SAR provenance")
            if statuses - {"domain-reviewed"}:
                raise ValueError("pipeline benchmarks require domain-reviewed labels")
        return self


class RateMetric(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    numerator: int = Field(ge=0)
    denominator: int = Field(ge=0)
    value: float | None = Field(default=None, ge=0, le=1)


class CandidateMetrics(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    true_positive_count: int = Field(ge=0)
    false_positive_count: int = Field(ge=0)
    false_negative_count: int = Field(ge=0)
    precision: RateMetric
    recall: RateMetric
    f1: RateMetric


class PixelMetrics(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    evaluated_pixel_count: int = Field(gt=0)
    true_positive_pixel_count: int = Field(ge=0)
    false_positive_pixel_count: int = Field(ge=0)
    false_negative_pixel_count: int = Field(ge=0)
    true_negative_pixel_count: int = Field(ge=0)
    precision: RateMetric
    recall: RateMetric
    intersection_over_union: RateMetric
    f1: RateMetric


class RegionMetrics(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    matched_region_count: int = Field(ge=0)
    reference_region_count: int = Field(ge=0)
    matched_iou_sum: float = Field(ge=0)
    mean_matched_iou: float | None = Field(default=None, ge=0, le=1)


class CaseEvaluationResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    case_id: str
    fixture_id: str
    review_statuses: tuple[ReviewStatus, ...]
    candidate_metrics: CandidateMetrics
    pixel_metrics: PixelMetrics
    region_metrics: RegionMetrics
    false_positive_classes: dict[str, int]
    unclassified_false_positive_count: int = Field(ge=0)
    limitations: tuple[str, ...]


class EvaluationReport(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    evaluation_report_version: Literal["1.0.0"] = "1.0.0"
    evaluation_set_id: str
    evaluation_set_version: str
    purpose: str
    candidate_iou_threshold: float
    software_commit: str
    case_results: tuple[CaseEvaluationResult, ...]
    candidate_metrics: CandidateMetrics
    pixel_metrics: PixelMetrics
    region_metrics: RegionMetrics
    false_positive_classes: dict[str, int]
    unclassified_false_positive_count: int = Field(ge=0)
    limitations: tuple[str, ...]
