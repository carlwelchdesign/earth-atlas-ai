from __future__ import annotations

import json
from pathlib import Path

import pytest

from echoatlas.evaluation import EvaluationInputError, evaluate_set

SOFTWARE_COMMIT = "b" * 40
REPOSITORY_ROOT = Path(__file__).parents[3]
SYNTHETIC_SET = REPOSITORY_ROOT / "fixtures/evaluation/synthetic-v1/evaluation-set.json"


def _fixture_documents() -> tuple[dict[str, object], dict[str, object]]:
    manifest = json.loads(SYNTHETIC_SET.read_text())
    predictions = json.loads((SYNTHETIC_SET.parent / "predictions.geojson").read_text())
    return manifest, predictions


def _write_fixture(root: Path, manifest: dict[str, object], predictions: dict[str, object]) -> Path:
    root.mkdir()
    manifest_path = root / "evaluation-set.json"
    manifest_path.write_text(json.dumps(manifest))
    (root / "predictions.geojson").write_text(json.dumps(predictions))
    return manifest_path


def _first_case(manifest: dict[str, object]) -> dict[str, object]:
    cases = manifest["cases"]
    assert isinstance(cases, list)
    case = cases[0]
    assert isinstance(case, dict)
    return case


def test_synthetic_baseline_reports_explicit_candidate_pixel_and_region_grain() -> None:
    report = evaluate_set(SYNTHETIC_SET, software_commit=SOFTWARE_COMMIT)

    assert report.purpose == "software-verification"
    assert report.software_commit == SOFTWARE_COMMIT
    assert report.candidate_metrics.true_positive_count == 1
    assert report.candidate_metrics.false_positive_count == 6
    assert report.candidate_metrics.false_negative_count == 0
    assert report.candidate_metrics.precision.model_dump() == {
        "numerator": 1,
        "denominator": 7,
        "value": pytest.approx(1 / 7),
    }
    assert report.candidate_metrics.recall.value == 1
    assert report.candidate_metrics.f1.value == 0.25
    assert report.pixel_metrics.evaluated_pixel_count == 600
    assert report.pixel_metrics.true_positive_pixel_count == 9
    assert report.pixel_metrics.false_positive_pixel_count == 21
    assert report.pixel_metrics.false_negative_pixel_count == 0
    assert report.pixel_metrics.true_negative_pixel_count == 570
    assert report.pixel_metrics.precision.value == 0.3
    assert report.pixel_metrics.intersection_over_union.value == 0.3
    assert report.region_metrics.matched_region_count == 1
    assert report.region_metrics.reference_region_count == 1
    assert report.region_metrics.mean_matched_iou == 1
    assert report.false_positive_classes == {
        "geometry": 1,
        "water-moisture": 1,
        "speckle": 1,
        "shadow-layover": 1,
        "registration-artifact": 1,
        "other": 1,
    }
    assert report.unclassified_false_positive_count == 0
    assert report.case_results[0].review_statuses == ("synthetic-established",)


def test_empty_case_rates_are_null_instead_of_zero(tmp_path: Path) -> None:
    manifest, predictions = _fixture_documents()
    case = _first_case(manifest)
    case["reference_regions"] = []
    case["false_positive_annotations"] = []
    predictions["features"] = []
    path = _write_fixture(tmp_path / "empty", manifest, predictions)

    report = evaluate_set(path, software_commit=SOFTWARE_COMMIT)

    assert report.candidate_metrics.precision.value is None
    assert report.candidate_metrics.recall.value is None
    assert report.candidate_metrics.f1.value is None
    assert report.pixel_metrics.precision.value is None
    assert report.pixel_metrics.recall.value is None
    assert report.pixel_metrics.intersection_over_union.value is None
    assert report.pixel_metrics.f1.value is None
    assert report.region_metrics.mean_matched_iou is None
    assert report.pixel_metrics.true_negative_pixel_count == 600


def test_candidates_outside_reviewed_geometry_do_not_enter_denominators(
    tmp_path: Path,
) -> None:
    manifest, predictions = _fixture_documents()
    case = _first_case(manifest)
    case["evaluation_geometry"] = {
        "type": "Polygon",
        "coordinates": [[[0, 0], [5, 0], [5, 20], [0, 20], [0, 0]]],
    }
    case["false_positive_annotations"] = []
    path = _write_fixture(tmp_path / "reviewed-extent", manifest, predictions)

    report = evaluate_set(path, software_commit=SOFTWARE_COMMIT)

    assert report.candidate_metrics.true_positive_count == 1
    assert report.candidate_metrics.false_positive_count == 0
    assert report.candidate_metrics.precision.value == 1
    assert report.pixel_metrics.evaluated_pixel_count == 100


def test_evaluation_fixture_cannot_overlap_tuning_set(tmp_path: Path) -> None:
    manifest, predictions = _fixture_documents()
    case = _first_case(manifest)
    manifest["tuning_fixture_ids"] = [case["fixture_id"]]
    path = _write_fixture(tmp_path / "overlap", manifest, predictions)

    with pytest.raises(EvaluationInputError, match="overlap tuning fixtures"):
        evaluate_set(path, software_commit=SOFTWARE_COMMIT)


def test_reviewed_labels_require_reviewer_identity_and_timestamp(tmp_path: Path) -> None:
    manifest, predictions = _fixture_documents()
    case = _first_case(manifest)
    regions = case["reference_regions"]
    assert isinstance(regions, list)
    regions[0]["review_status"] = "domain-reviewed"
    path = _write_fixture(tmp_path / "review", manifest, predictions)

    with pytest.raises(EvaluationInputError, match="reviewed labels require reviewer"):
        evaluate_set(path, software_commit=SOFTWARE_COMMIT)


def test_pending_labels_cannot_enter_metric_denominators(tmp_path: Path) -> None:
    manifest, predictions = _fixture_documents()
    case = _first_case(manifest)
    regions = case["reference_regions"]
    assert isinstance(regions, list)
    regions[0]["review_status"] = "pending"
    path = _write_fixture(tmp_path / "pending", manifest, predictions)

    with pytest.raises(EvaluationInputError, match="pending labels cannot enter"):
        evaluate_set(path, software_commit=SOFTWARE_COMMIT)


def test_pipeline_benchmark_rejects_synthetic_provenance(tmp_path: Path) -> None:
    manifest, predictions = _fixture_documents()
    manifest["purpose"] = "pipeline-benchmark"
    path = _write_fixture(tmp_path / "pipeline", manifest, predictions)

    with pytest.raises(
        EvaluationInputError, match="pipeline benchmarks require derived public SAR"
    ):
        evaluate_set(path, software_commit=SOFTWARE_COMMIT)


def test_false_positive_annotations_cannot_relabel_a_match(tmp_path: Path) -> None:
    manifest, predictions = _fixture_documents()
    case = _first_case(manifest)
    annotations = case["false_positive_annotations"]
    assert isinstance(annotations, list)
    annotations.append(
        {
            "candidate_id": "candidate-match",
            "failure_class": "other",
            "review_status": "synthetic-established",
            "reviewer": None,
            "reviewed_at": None,
        }
    )
    path = _write_fixture(tmp_path / "matched-annotation", manifest, predictions)

    with pytest.raises(EvaluationInputError, match="not false positives: candidate-match"):
        evaluate_set(path, software_commit=SOFTWARE_COMMIT)


def test_prediction_paths_must_remain_inside_set_directory(tmp_path: Path) -> None:
    manifest, predictions = _fixture_documents()
    case = _first_case(manifest)
    case["prediction_path"] = "../predictions.geojson"
    path = _write_fixture(tmp_path / "path", manifest, predictions)

    with pytest.raises(EvaluationInputError, match="must stay inside"):
        evaluate_set(path, software_commit=SOFTWARE_COMMIT)
