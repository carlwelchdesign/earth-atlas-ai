import json
import threading
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from echoatlas.analysis_jobs import (
    AnalysisJobError,
    AnalysisJobService,
    AnalysisProcessingError,
    AnalysisSelectionError,
    AnalysisSelectionManifest,
    AnalysisSelectionRequest,
    PreparedBundleRunner,
    create_selection_manifest,
)
from echoatlas.processor.catalog.search_models import (
    CatalogLicense,
    CatalogSearchItem,
    CatalogSourceIdentity,
    GeoJsonPolygon,
    SearchAoi,
)

NOW = datetime(2026, 8, 25, 20, tzinfo=UTC)


def _polygon(west: float = -112.2, east: float = -112.05) -> GeoJsonPolygon:
    return GeoJsonPolygon(
        coordinates=(
            (
                (west, 40.45),
                (east, 40.45),
                (east, 40.6),
                (west, 40.6),
                (west, 40.45),
            ),
        )
    )


def _item(
    role: str,
    *,
    provider: str = "umbra",
    acquired_at: datetime | None = None,
    west: float = -112.2,
    east: float = -112.05,
) -> CatalogSearchItem:
    host = (
        "umbra-open-data-catalog.s3.us-west-2.amazonaws.com"
        if provider == "umbra"
        else "stac.dataspace.copernicus.eu"
    )
    return CatalogSearchItem(
        provider=provider,
        acquired_at=acquired_at or (NOW if role == "before" else NOW + timedelta(days=25)),
        bbox=(west, 40.45, east, 40.6),
        footprint=_polygon(west, east),
        product_type="GEC" if provider == "umbra" else "IW_GRDH_1S_C",
        polarizations=("VV",),
        resolution_range_m=0.5 if provider == "umbra" else 10,
        resolution_azimuth_m=0.5 if provider == "umbra" else 10,
        platform="Umbra-05" if provider == "umbra" else "sentinel-1c",
        observation_direction="left" if provider == "umbra" else "right",
        orbit_state="ascending",
        incidence_angle_deg=40,
        license=CatalogLicense(
            label="CC-BY-4.0" if provider == "umbra" else "Copernicus notice",
            url="https://creativecommons.org/licenses/by/4.0/"
            if provider == "umbra"
            else "https://dataspace.copernicus.eu/terms-and-conditions",
        ),
        source=CatalogSourceIdentity(
            item_id=f"{provider}-{role}",
            collection="umbra-2025" if provider == "umbra" else "sentinel-1-grd",
            href=f"https://{host}/items/{provider}-{role}.json",
        ),
    )


def _request(*, provider: str = "umbra") -> AnalysisSelectionRequest:
    return AnalysisSelectionRequest(
        aoi=SearchAoi(bbox=(-112.2, 40.45, -112.05, 40.6), geometry=_polygon()),
        before=_item("before", provider=provider),
        after=_item("after", provider=provider),
    )


def _manifest(*, provider: str = "umbra") -> AnalysisSelectionManifest:
    return create_selection_manifest(_request(provider=provider), clock=lambda: NOW)


def _bundle(manifest: AnalysisSelectionManifest) -> dict[str, object]:
    return {
        "contractVersion": "1.0.0",
        "bundleId": f"bundle-{manifest.selection_id}",
        "acquisitions": [
            {"role": "before", "id": manifest.before.source.item_id},
            {"role": "after", "id": manifest.after.source.item_id},
        ],
    }


class ImmediateRunner:
    def run(
        self, manifest: AnalysisSelectionManifest, cancelled: threading.Event
    ) -> dict[str, object]:
        if cancelled.is_set():
            raise AnalysisProcessingError("Preparation was cancelled.")
        return _bundle(manifest)


class FailingRunner:
    def run(
        self, manifest: AnalysisSelectionManifest, cancelled: threading.Event
    ) -> dict[str, object]:
        raise AnalysisProcessingError("Configured fixture processing failed safely.")


class BlockingRunner:
    def __init__(self) -> None:
        self.started = threading.Event()
        self.release = threading.Event()

    def run(
        self, manifest: AnalysisSelectionManifest, cancelled: threading.Event
    ) -> dict[str, object]:
        self.started.set()
        self.release.wait(timeout=2)
        if cancelled.is_set():
            raise AnalysisProcessingError("Preparation was cancelled.")
        return _bundle(manifest)


def _await_terminal(service: AnalysisJobService, job_id: str):
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        view = service.get(job_id)
        if view.status in {"succeeded", "failed", "cancelled"}:
            return view
        time.sleep(0.01)
    raise AssertionError("analysis job did not reach a terminal state")


@pytest.mark.parametrize("provider", ["umbra", "sentinel-1"])
def test_selection_manifest_is_hashed_and_retains_provider_provenance(provider: str) -> None:
    manifest = _manifest(provider=provider)

    assert manifest.selection_id.startswith("selection-")
    assert len(manifest.aoi_geometry_sha256) == 64
    assert len(manifest.manifest_sha256) == 64
    assert manifest.before.provider == provider
    assert manifest.before.source.item_id == f"{provider}-before"
    assert manifest.after.license.label
    assert manifest.comparability.before_overlap_percent == 100
    assert manifest.comparability.scientific_validity == "not_determined"
    assert "does not establish scientific validity" in manifest.interpretation_limits[0]


def test_selection_manifest_rejects_wrong_order_non_overlap_and_forged_source() -> None:
    reversed_request = _request().model_copy(
        update={
            "before": _item("before", acquired_at=NOW + timedelta(days=2)),
            "after": _item("after", acquired_at=NOW),
        }
    )
    with pytest.raises(AnalysisSelectionError, match="before acquisition must precede"):
        create_selection_manifest(reversed_request, clock=lambda: NOW)

    non_overlap = _request().model_copy(update={"after": _item("after", west=-111.9, east=-111.8)})
    with pytest.raises(AnalysisSelectionError, match="polygonal intersection"):
        create_selection_manifest(non_overlap, clock=lambda: NOW)

    forged = _request().model_copy(
        update={
            "before": _item("before").model_copy(
                update={
                    "source": CatalogSourceIdentity(
                        item_id="umbra-before",
                        collection="umbra-2025",
                        href="https://attacker.example/items/umbra-before.json",
                    )
                }
            )
        }
    )
    with pytest.raises(AnalysisSelectionError, match="allowlisted HTTPS"):
        create_selection_manifest(forged, clock=lambda: NOW)


def test_manifest_rejects_content_tampering() -> None:
    document = _manifest().model_dump(mode="json")
    document["before"]["source"]["item_id"] = "changed"

    with pytest.raises(ValidationError, match="checksum"):
        AnalysisSelectionManifest.model_validate(document)


def test_job_succeeds_and_returns_matching_bundle() -> None:
    service = AnalysisJobService(ImmediateRunner(), clock=lambda: NOW)
    created = service.create(_manifest())
    completed = _await_terminal(service, created.job_id)

    assert created.status in {"queued", "running", "succeeded"}
    assert completed.status == "succeeded"
    assert completed.bundle is not None
    assert completed.error is None


def test_job_failure_can_retry_with_the_same_manifest() -> None:
    service = AnalysisJobService(FailingRunner(), clock=lambda: NOW)
    failed = _await_terminal(service, service.create(_manifest()).job_id)

    assert failed.status == "failed"
    assert failed.error == "Configured fixture processing failed safely."
    retried = service.retry(failed.job_id, failed.manifest.manifest_sha256)
    assert retried.retry_of == failed.job_id
    with pytest.raises(AnalysisJobError, match="checksum"):
        service.retry(failed.job_id, "0" * 64)


def test_running_job_can_be_cancelled_and_does_not_publish_a_bundle() -> None:
    runner = BlockingRunner()
    service = AnalysisJobService(runner, clock=lambda: NOW)
    created = service.create(_manifest())
    assert runner.started.wait(timeout=1)

    cancelled = service.cancel(created.job_id)
    runner.release.set()
    terminal = _await_terminal(service, created.job_id)

    assert cancelled.status == "cancelled"
    assert terminal.status == "cancelled"
    assert terminal.bundle is None


def test_queue_capacity_fails_safely_while_jobs_are_active() -> None:
    runner = BlockingRunner()
    service = AnalysisJobService(runner, clock=lambda: NOW, max_jobs=1)
    created = service.create(_manifest())
    assert runner.started.wait(timeout=1)

    with pytest.raises(AnalysisJobError, match="queue is full"):
        service.create(_manifest())
    service.cancel(created.job_id)
    runner.release.set()


def test_prepared_bundle_runner_validates_size_contract_and_selected_identities(
    tmp_path: Path,
) -> None:
    manifest = _manifest()
    bundle_path = tmp_path / "bundle.json"
    bundle_path.write_text(json.dumps(_bundle(manifest)))
    runner = PreparedBundleRunner(bundle_path)

    assert runner.run(manifest, threading.Event())["contractVersion"] == "1.0.0"

    mismatch = _bundle(manifest)
    mismatch["acquisitions"][1]["id"] = "wrong-after"  # type: ignore[index]
    bundle_path.write_text(json.dumps(mismatch))
    with pytest.raises(AnalysisProcessingError, match="does not match"):
        runner.run(manifest, threading.Event())

    with pytest.raises(AnalysisProcessingError, match="No prepared bundle"):
        PreparedBundleRunner(None).run(manifest, threading.Event())
