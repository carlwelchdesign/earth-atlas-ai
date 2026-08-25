"""Pure evaluation policy with file I/O restricted to the manifest edge."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import cast

import numpy as np
from affine import Affine
from numpy.typing import NDArray
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from rasterio.errors import RasterioError  # type: ignore[import-untyped]
from rasterio.features import rasterize  # type: ignore[import-untyped]
from rasterio.warp import transform_geom  # type: ignore[import-untyped]

from echoatlas.evaluation.models import (
    CandidateMetrics,
    CaseEvaluationResult,
    EvaluationCase,
    EvaluationReport,
    EvaluationSet,
    FailureClass,
    PixelMetrics,
    RateMetric,
    RegionMetrics,
    ReviewStatus,
)

BooleanMask = NDArray[np.bool_]
FloatMatrix = NDArray[np.float64]

FAILURE_CLASSES: tuple[FailureClass, ...] = (
    "geometry",
    "water-moisture",
    "speckle",
    "shadow-layover",
    "registration-artifact",
    "other",
)


class EvaluationInputError(ValueError):
    """Raised when an evaluation set or candidate collection is unusable."""


class _PredictionFeature(BaseModel):
    model_config = ConfigDict(frozen=True, extra="allow")

    type: str
    id: str = Field(min_length=1)
    geometry: dict[str, object]


class _PredictionCollection(BaseModel):
    model_config = ConfigDict(frozen=True, extra="allow")

    type: str
    features: tuple[_PredictionFeature, ...]


def evaluate_set(
    evaluation_set_path: Path,
    *,
    software_commit: str,
) -> EvaluationReport:
    """Load, validate, and evaluate every case in an evaluation manifest."""

    evaluation_set = _read_model(evaluation_set_path, EvaluationSet, "evaluation set")
    case_results = tuple(
        _evaluate_case(evaluation_set_path.parent, case, evaluation_set.candidate_iou_threshold)
        for case in evaluation_set.cases
    )
    return _aggregate_report(evaluation_set, case_results, software_commit)


def _evaluate_case(root: Path, case: EvaluationCase, threshold: float) -> CaseEvaluationResult:
    prediction_path = _resolve_child(root, case.prediction_path)
    predictions = _read_model(prediction_path, _PredictionCollection, "prediction collection")
    if predictions.type != "FeatureCollection":
        raise EvaluationInputError("prediction collection type must be FeatureCollection")
    prediction_ids = [feature.id for feature in predictions.features]
    if len(prediction_ids) != len(set(prediction_ids)):
        raise EvaluationInputError(f"case {case.case_id} has duplicate candidate IDs")

    evaluation_mask = _rasterize_geometry(case.evaluation_geometry, case)
    reference_masks = []
    for region in case.reference_regions:
        mask = _rasterize_geometry(region.geometry, case) & evaluation_mask
        if not np.any(mask):
            raise EvaluationInputError(
                f"case {case.case_id} reference {region.region_id} has no pixels "
                "inside the evaluated geometry"
            )
        reference_masks.append(mask)
    prediction_ids, overlaps, predicted_union = _evaluate_predictions(
        predictions, reference_masks, evaluation_mask, case
    )
    matches = _maximum_threshold_matching(overlaps, threshold)
    matched_predictions = {prediction_index for prediction_index, _ in matches}
    matched_references = {reference_index for _, reference_index in matches}
    false_positive_ids = {
        prediction_ids[index]
        for index in range(len(prediction_ids))
        if index not in matched_predictions
    }
    annotations = {item.candidate_id: item for item in case.false_positive_annotations}
    unknown_annotations = sorted(set(annotations) - false_positive_ids)
    if unknown_annotations:
        raise EvaluationInputError(
            f"case {case.case_id} annotates candidates that are not false positives: "
            f"{', '.join(unknown_annotations)}"
        )

    class_counts = Counter(
        annotations[candidate_id].failure_class
        for candidate_id in false_positive_ids
        if candidate_id in annotations
    )
    true_positive_count = len(matches)
    false_positive_count = len(prediction_ids) - len(matched_predictions)
    false_negative_count = len(reference_masks) - len(matched_references)
    candidate_metrics = _candidate_metrics(
        true_positive_count, false_positive_count, false_negative_count
    )
    pixel_metrics = _pixel_metrics(predicted_union, reference_masks, evaluation_mask)
    iou_sum = sum(float(overlaps[prediction, reference]) for prediction, reference in matches)
    statuses = cast(
        tuple[ReviewStatus, ...],
        tuple(
            sorted(
                {
                    *(region.review_status for region in case.reference_regions),
                    *(item.review_status for item in case.false_positive_annotations),
                }
            )
        ),
    )
    return CaseEvaluationResult(
        case_id=case.case_id,
        fixture_id=case.fixture_id,
        review_statuses=statuses,
        candidate_metrics=candidate_metrics,
        pixel_metrics=pixel_metrics,
        region_metrics=RegionMetrics(
            matched_region_count=len(matches),
            reference_region_count=len(reference_masks),
            matched_iou_sum=iou_sum,
            mean_matched_iou=iou_sum / len(matches) if matches else None,
        ),
        false_positive_classes={name: class_counts[name] for name in FAILURE_CLASSES},
        unclassified_false_positive_count=false_positive_count - sum(class_counts.values()),
        limitations=case.limitations,
    )


def _aggregate_report(
    evaluation_set: EvaluationSet,
    cases: tuple[CaseEvaluationResult, ...],
    software_commit: str,
) -> EvaluationReport:
    true_positives = sum(case.candidate_metrics.true_positive_count for case in cases)
    false_positives = sum(case.candidate_metrics.false_positive_count for case in cases)
    false_negatives = sum(case.candidate_metrics.false_negative_count for case in cases)
    evaluated_pixels = sum(case.pixel_metrics.evaluated_pixel_count for case in cases)
    pixel_true_positives = sum(case.pixel_metrics.true_positive_pixel_count for case in cases)
    pixel_false_positives = sum(case.pixel_metrics.false_positive_pixel_count for case in cases)
    pixel_false_negatives = sum(case.pixel_metrics.false_negative_pixel_count for case in cases)
    pixel_true_negatives = sum(case.pixel_metrics.true_negative_pixel_count for case in cases)
    matched_regions = sum(case.region_metrics.matched_region_count for case in cases)
    reference_regions = sum(case.region_metrics.reference_region_count for case in cases)
    matched_iou_sum = sum(case.region_metrics.matched_iou_sum for case in cases)
    class_counts: dict[str, int] = {
        name: sum(case.false_positive_classes[name] for case in cases) for name in FAILURE_CLASSES
    }
    return EvaluationReport(
        evaluation_set_id=evaluation_set.evaluation_set_id,
        evaluation_set_version=evaluation_set.evaluation_set_version,
        purpose=evaluation_set.purpose,
        candidate_iou_threshold=evaluation_set.candidate_iou_threshold,
        software_commit=software_commit,
        case_results=cases,
        candidate_metrics=_candidate_metrics(true_positives, false_positives, false_negatives),
        pixel_metrics=_pixel_metrics_from_counts(
            evaluated_pixels,
            pixel_true_positives,
            pixel_false_positives,
            pixel_false_negatives,
            pixel_true_negatives,
        ),
        region_metrics=RegionMetrics(
            matched_region_count=matched_regions,
            reference_region_count=reference_regions,
            matched_iou_sum=matched_iou_sum,
            mean_matched_iou=matched_iou_sum / matched_regions if matched_regions else None,
        ),
        false_positive_classes=class_counts,
        unclassified_false_positive_count=sum(
            case.unclassified_false_positive_count for case in cases
        ),
        limitations=evaluation_set.limitations,
    )


def _rasterize_geometry(
    geometry: dict[str, object],
    case: EvaluationCase,
    *,
    allow_empty: bool = False,
) -> BooleanMask:
    try:
        projected = cast(
            dict[str, object],
            transform_geom(case.geometry_crs, case.grid.crs, geometry, precision=9),
        )
        mask = cast(
            BooleanMask,
            rasterize(
                [(projected, 1)],
                out_shape=(case.grid.height, case.grid.width),
                transform=Affine(*case.grid.transform),
                fill=0,
                dtype="uint8",
                all_touched=False,
            ).astype(bool),
        )
    except (RasterioError, TypeError, ValueError) as error:
        raise EvaluationInputError(f"case {case.case_id} contains invalid geometry") from error
    if not allow_empty and not np.any(mask):
        raise EvaluationInputError(
            f"case {case.case_id} contains a region with no pixels on its evaluation grid"
        )
    return mask


def _evaluate_predictions(
    predictions: _PredictionCollection,
    references: list[BooleanMask],
    evaluation_mask: BooleanMask,
    case: EvaluationCase,
) -> tuple[list[str], FloatMatrix, BooleanMask]:
    prediction_ids: list[str] = []
    overlap_rows: list[list[float]] = []
    predicted_union = np.zeros_like(evaluation_mask)
    reference_areas = [int(np.count_nonzero(reference)) for reference in references]
    for feature in predictions.features:
        prediction = _rasterize_geometry(feature.geometry, case, allow_empty=True) & evaluation_mask
        prediction_area = int(np.count_nonzero(prediction))
        if prediction_area == 0:
            continue
        prediction_ids.append(feature.id)
        predicted_union |= prediction
        row = []
        for reference, reference_area in zip(references, reference_areas, strict=True):
            intersection = int(np.count_nonzero(prediction & reference))
            union = prediction_area + reference_area - intersection
            row.append(intersection / union)
        overlap_rows.append(row)
    overlaps = np.asarray(overlap_rows, dtype=np.float64)
    if not overlap_rows:
        overlaps = np.zeros((0, len(references)), dtype=np.float64)
    return prediction_ids, overlaps, predicted_union


def _maximum_threshold_matching(overlaps: FloatMatrix, threshold: float) -> list[tuple[int, int]]:
    reference_to_prediction: dict[int, int] = {}

    def assign(prediction: int, visited: set[int]) -> bool:
        eligible = [
            reference
            for reference in range(overlaps.shape[1])
            if overlaps[prediction, reference] >= threshold
        ]
        eligible.sort(key=lambda reference: (-overlaps[prediction, reference], reference))
        for reference in eligible:
            if reference in visited:
                continue
            visited.add(reference)
            current = reference_to_prediction.get(reference)
            if current is None or assign(current, visited):
                reference_to_prediction[reference] = prediction
                return True
        return False

    for prediction in range(overlaps.shape[0]):
        assign(prediction, set())
    return sorted(
        (prediction, reference) for reference, prediction in reference_to_prediction.items()
    )


def _candidate_metrics(
    true_positives: int, false_positives: int, false_negatives: int
) -> CandidateMetrics:
    return CandidateMetrics(
        true_positive_count=true_positives,
        false_positive_count=false_positives,
        false_negative_count=false_negatives,
        precision=_rate(true_positives, true_positives + false_positives),
        recall=_rate(true_positives, true_positives + false_negatives),
        f1=_rate(2 * true_positives, 2 * true_positives + false_positives + false_negatives),
    )


def _pixel_metrics(
    predicted: BooleanMask,
    references: list[BooleanMask],
    evaluation_mask: BooleanMask,
) -> PixelMetrics:
    expected = np.zeros_like(predicted)
    for mask in references:
        expected |= mask
    true_positives = int(np.count_nonzero(predicted & expected))
    false_positives = int(np.count_nonzero(predicted & ~expected))
    false_negatives = int(np.count_nonzero(~predicted & expected))
    true_negatives = int(np.count_nonzero(evaluation_mask & ~predicted & ~expected))
    return _pixel_metrics_from_counts(
        int(np.count_nonzero(evaluation_mask)),
        true_positives,
        false_positives,
        false_negatives,
        true_negatives,
    )


def _pixel_metrics_from_counts(
    evaluated: int,
    true_positives: int,
    false_positives: int,
    false_negatives: int,
    true_negatives: int,
) -> PixelMetrics:
    return PixelMetrics(
        evaluated_pixel_count=evaluated,
        true_positive_pixel_count=true_positives,
        false_positive_pixel_count=false_positives,
        false_negative_pixel_count=false_negatives,
        true_negative_pixel_count=true_negatives,
        precision=_rate(true_positives, true_positives + false_positives),
        recall=_rate(true_positives, true_positives + false_negatives),
        intersection_over_union=_rate(
            true_positives, true_positives + false_positives + false_negatives
        ),
        f1=_rate(2 * true_positives, 2 * true_positives + false_positives + false_negatives),
    )


def _rate(numerator: int, denominator: int) -> RateMetric:
    return RateMetric(
        numerator=numerator,
        denominator=denominator,
        value=numerator / denominator if denominator else None,
    )


def _resolve_child(root: Path, relative_path: str) -> Path:
    candidate = (root / relative_path).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as error:
        raise EvaluationInputError(
            "prediction path must stay inside the evaluation-set directory"
        ) from error
    return candidate


def _read_model[T: BaseModel](path: Path, model: type[T], label: str) -> T:
    try:
        document = json.loads(path.read_text())
        return model.model_validate(document)
    except OSError as error:
        raise EvaluationInputError(f"{label} could not be read: {path}") from error
    except json.JSONDecodeError as error:
        raise EvaluationInputError(f"{label} is not valid JSON: {path}") from error
    except ValidationError as error:
        raise EvaluationInputError(f"{label} failed validation: {error}") from error
