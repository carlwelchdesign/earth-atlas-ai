"""Immutable Explore selections and bounded preparation-job orchestration."""

from __future__ import annotations

import hashlib
import json
import os
import threading
from collections.abc import Callable, Mapping
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, Protocol
from urllib.parse import urlparse
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from echoatlas.processor.catalog.models import Acquisition
from echoatlas.processor.catalog.search_models import CatalogSearchItem, SearchAoi
from echoatlas.processor.selection import PairComparability, compare_pair

ANALYSIS_SELECTION_CONTRACT_VERSION: Literal["1.0.0"] = "1.0.0"
MAX_BUNDLE_BYTES = 10_000_000
SOURCE_HOSTS = {
    "umbra": "umbra-open-data-catalog.s3.us-west-2.amazonaws.com",
    "sentinel-1": "stac.dataspace.copernicus.eu",
}


class AnalysisSelectionError(ValueError):
    """Raised when a proposed pair cannot form a safe immutable selection."""


class AnalysisJobError(ValueError):
    """Raised when a job operation violates the bounded state contract."""


class AnalysisProcessingError(RuntimeError):
    """Raised when the configured deterministic runner cannot produce a bundle."""


class ProcessingInputs(BaseModel):
    model_config = ConfigDict(frozen=True)

    preset: Literal["echoatlas-standard-v1"] = "echoatlas-standard-v1"
    normalization: Literal["robust-percentile"] = "robust-percentile"
    resampling: Literal["bilinear"] = "bilinear"
    score_method: Literal["absolute-difference"] = "absolute-difference"
    score_threshold: float = 0.65
    minimum_component_pixels: int = 48


class SelectionComparability(BaseModel):
    model_config = ConfigDict(frozen=True)

    temporal_separation_seconds: float = Field(gt=0)
    common_footprint: dict[str, Any]
    common_bbox: tuple[float, float, float, float]
    before_overlap_percent: float = Field(ge=0, le=100)
    after_overlap_percent: float = Field(ge=0, le=100)
    same_product: bool
    shared_polarizations: tuple[str, ...]
    range_resolution_delta_percent: float = Field(ge=0)
    azimuth_resolution_delta_percent: float = Field(ge=0)
    same_observation_direction: bool
    same_orbit_state: bool
    incidence_angle_delta_deg: float | None = Field(default=None, ge=0)
    warnings: tuple[str, ...]
    scientific_validity: Literal["not_determined"] = "not_determined"


class AnalysisSelectionRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    contract_version: Literal["1.0.0"] = ANALYSIS_SELECTION_CONTRACT_VERSION
    aoi: SearchAoi
    before: CatalogSearchItem
    after: CatalogSearchItem
    processing_inputs: ProcessingInputs = ProcessingInputs()


class AnalysisSelectionContent(BaseModel):
    model_config = ConfigDict(frozen=True)

    contract_version: Literal["1.0.0"] = ANALYSIS_SELECTION_CONTRACT_VERSION
    selection_id: str
    created_at: datetime
    aoi: SearchAoi
    aoi_geometry_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    before: CatalogSearchItem
    after: CatalogSearchItem
    comparability: SelectionComparability
    processing_inputs: ProcessingInputs
    interpretation_limits: tuple[str, ...]


class AnalysisSelectionManifest(AnalysisSelectionContent):
    manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def validate_checksum(self) -> AnalysisSelectionManifest:
        content = AnalysisSelectionContent.model_validate(
            self.model_dump(mode="json", exclude={"manifest_sha256"})
        )
        if _model_sha256(content) != self.manifest_sha256:
            raise ValueError("selection manifest checksum does not match its content")
        return self


class AnalysisJobCreateRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    manifest: AnalysisSelectionManifest


class AnalysisJobRetryRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class AnalysisJobView(BaseModel):
    model_config = ConfigDict(frozen=True)

    contract_version: Literal["1.0.0"] = ANALYSIS_SELECTION_CONTRACT_VERSION
    job_id: str
    retry_of: str | None = None
    status: Literal["queued", "running", "succeeded", "failed", "cancelled"]
    manifest: AnalysisSelectionManifest
    created_at: datetime
    updated_at: datetime
    error: str | None = None
    bundle: dict[str, Any] | None = None


class AnalysisRunner(Protocol):
    def run(
        self, manifest: AnalysisSelectionManifest, cancelled: threading.Event
    ) -> dict[str, Any]: ...


class PreparedBundleRunner:
    """Load a previously validated deterministic bundle for the exact selected pair."""

    def __init__(self, bundle_path: Path | None, *, max_bytes: int = MAX_BUNDLE_BYTES) -> None:
        self._bundle_path = bundle_path
        self._max_bytes = max_bytes

    def run(
        self, manifest: AnalysisSelectionManifest, cancelled: threading.Event
    ) -> dict[str, Any]:
        if cancelled.is_set():
            raise AnalysisProcessingError("Preparation was cancelled.")
        if self._bundle_path is None:
            raise AnalysisProcessingError(
                "No prepared bundle is configured for this selection. Prepare the licensed "
                "source pair first, then retry."
            )
        try:
            resolved = self._bundle_path.resolve(strict=True)
            size = resolved.stat().st_size
        except OSError as error:
            raise AnalysisProcessingError(
                "The configured prepared bundle is unavailable."
            ) from error
        if size > self._max_bytes:
            raise AnalysisProcessingError("The configured prepared bundle exceeds the size limit.")
        try:
            payload = resolved.read_bytes()
            document: Any = json.loads(payload)
        except (OSError, json.JSONDecodeError, UnicodeDecodeError) as error:
            raise AnalysisProcessingError("The configured prepared bundle is invalid.") from error
        if cancelled.is_set():
            raise AnalysisProcessingError("Preparation was cancelled.")
        if not isinstance(document, dict) or document.get("contractVersion") != "1.0.0":
            raise AnalysisProcessingError("The configured prepared bundle has an invalid contract.")
        acquisitions = document.get("acquisitions")
        if not isinstance(acquisitions, list):
            raise AnalysisProcessingError(
                "The configured prepared bundle has invalid acquisitions."
            )
        identities = {
            item.get("role"): item.get("id") for item in acquisitions if isinstance(item, dict)
        }
        expected = {
            "before": manifest.before.source.item_id,
            "after": manifest.after.source.item_id,
        }
        if identities != expected:
            raise AnalysisProcessingError(
                "The configured prepared bundle does not match the selected acquisitions."
            )
        return document


class _JobRecord:
    def __init__(
        self,
        *,
        job_id: str,
        manifest: AnalysisSelectionManifest,
        now: datetime,
        retry_of: str | None,
    ) -> None:
        self.job_id = job_id
        self.manifest = manifest
        self.retry_of = retry_of
        self.status: Literal["queued", "running", "succeeded", "failed", "cancelled"] = "queued"
        self.created_at = now
        self.updated_at = now
        self.error: str | None = None
        self.bundle: dict[str, Any] | None = None
        self.cancelled = threading.Event()


class AnalysisJobService:
    """Thread-safe, bounded coordinator around an injected deterministic runner."""

    def __init__(
        self,
        runner: AnalysisRunner,
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        max_jobs: int = 32,
        executor: ThreadPoolExecutor | None = None,
    ) -> None:
        if max_jobs < 1:
            raise ValueError("max_jobs must be positive")
        self._runner = runner
        self._clock = clock
        self._max_jobs = max_jobs
        self._executor = executor or ThreadPoolExecutor(
            max_workers=2, thread_name_prefix="echoatlas-analysis"
        )
        self._records: dict[str, _JobRecord] = {}
        self._lock = threading.Lock()

    def create(self, manifest: AnalysisSelectionManifest) -> AnalysisJobView:
        return self._create(manifest, retry_of=None)

    def get(self, job_id: str) -> AnalysisJobView:
        with self._lock:
            return self._view(self._record(job_id))

    def cancel(self, job_id: str) -> AnalysisJobView:
        with self._lock:
            record = self._record(job_id)
            if record.status in {"succeeded", "failed", "cancelled"}:
                raise AnalysisJobError(f"Job {job_id} is already {record.status}.")
            record.cancelled.set()
            record.status = "cancelled"
            record.updated_at = self._clock()
            record.error = None
            return self._view(record)

    def retry(self, job_id: str, manifest_sha256: str) -> AnalysisJobView:
        with self._lock:
            record = self._record(job_id)
            if record.status not in {"failed", "cancelled"}:
                raise AnalysisJobError("Only failed or cancelled jobs can be retried.")
            if record.manifest.manifest_sha256 != manifest_sha256:
                raise AnalysisJobError("Retry manifest checksum does not match the original job.")
            manifest = record.manifest
        return self._create(manifest, retry_of=job_id)

    def _create(
        self, manifest: AnalysisSelectionManifest, *, retry_of: str | None
    ) -> AnalysisJobView:
        now = self._clock()
        with self._lock:
            terminal = [
                key
                for key, value in self._records.items()
                if value.status in {"succeeded", "failed", "cancelled"}
            ]
            while len(self._records) >= self._max_jobs and terminal:
                self._records.pop(terminal.pop(0))
            if len(self._records) >= self._max_jobs:
                raise AnalysisJobError("The bounded analysis queue is full. Try again later.")
            job_id = f"analysis-{uuid4().hex}"
            record = _JobRecord(job_id=job_id, manifest=manifest, now=now, retry_of=retry_of)
            self._records[job_id] = record
            view = self._view(record)
        self._executor.submit(self._run, job_id)
        return view

    def _run(self, job_id: str) -> None:
        with self._lock:
            record = self._record(job_id)
            if record.status == "cancelled":
                return
            record.status = "running"
            record.updated_at = self._clock()
            manifest = record.manifest
            cancelled = record.cancelled
        try:
            bundle = self._runner.run(manifest, cancelled)
        except Exception as error:  # runner errors are normalized at this boundary
            with self._lock:
                record = self._record(job_id)
                if record.status == "cancelled" or cancelled.is_set():
                    record.status = "cancelled"
                    record.error = None
                else:
                    record.status = "failed"
                    record.error = _safe_runner_error(error)
                record.updated_at = self._clock()
            return
        with self._lock:
            record = self._record(job_id)
            if record.status == "cancelled" or cancelled.is_set():
                record.status = "cancelled"
                record.bundle = None
            else:
                record.status = "succeeded"
                record.bundle = bundle
            record.updated_at = self._clock()

    def _record(self, job_id: str) -> _JobRecord:
        try:
            return self._records[job_id]
        except KeyError as error:
            raise AnalysisJobError("Analysis job was not found.") from error

    @staticmethod
    def _view(record: _JobRecord) -> AnalysisJobView:
        return AnalysisJobView(
            job_id=record.job_id,
            retry_of=record.retry_of,
            status=record.status,
            manifest=record.manifest,
            created_at=record.created_at,
            updated_at=record.updated_at,
            error=record.error,
            bundle=record.bundle,
        )


def create_selection_manifest(
    request: AnalysisSelectionRequest,
    *,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> AnalysisSelectionManifest:
    _validate_source_identity(request.before)
    _validate_source_identity(request.after)
    try:
        comparison = compare_pair(_as_acquisition(request.before), _as_acquisition(request.after))
    except ValueError as error:
        raise AnalysisSelectionError(str(error)) from error
    aoi_sha256 = _sha256_json(request.aoi.geometry.model_dump(mode="json"))
    comparison_view = _comparison_view(comparison)
    provisional = AnalysisSelectionContent(
        selection_id="pending",
        created_at=clock(),
        aoi=request.aoi,
        aoi_geometry_sha256=aoi_sha256,
        before=request.before,
        after=request.after,
        comparability=comparison_view,
        processing_inputs=request.processing_inputs,
        interpretation_limits=(
            "Comparability evidence does not establish scientific validity.",
            "Processing outputs are machine-generated candidates, not confirmed change.",
            (
                "Speckle, moisture, terrain, shadow, layover, geometry, and "
                "registration can create apparent differences."
            ),
        ),
    )
    identity_hash = _model_sha256(provisional)
    content = provisional.model_copy(update={"selection_id": f"selection-{identity_hash[:20]}"})
    return AnalysisSelectionManifest(**content.model_dump(), manifest_sha256=_model_sha256(content))


def build_default_analysis_job_service(
    environ: Mapping[str, str] | None = None,
) -> AnalysisJobService:
    environment = os.environ if environ is None else environ
    configured = environment.get("ECHOATLAS_PREPARED_BUNDLE_PATH", "").strip()
    path = Path(configured) if configured else None
    return AnalysisJobService(PreparedBundleRunner(path))


def _as_acquisition(item: CatalogSearchItem) -> Acquisition:
    return Acquisition(
        item_id=item.source.item_id,
        acquired_at=item.acquired_at,
        bbox=item.bbox,
        geometry=item.footprint.model_dump(mode="json"),
        product_type=item.product_type,
        polarizations=item.polarizations,
        resolution_range_m=item.resolution_range_m,
        resolution_azimuth_m=item.resolution_azimuth_m,
        platform=item.platform,
        observation_direction=item.observation_direction,
        orbit_state=item.orbit_state,
        incidence_angle_deg=item.incidence_angle_deg,
        grazing_angle_deg=None,
        license=item.license.label,
        source_url=item.source.href,
        provider_task_id=None,
        assets=(),
        source_document={},
    )


def _comparison_view(value: PairComparability) -> SelectionComparability:
    return SelectionComparability(
        temporal_separation_seconds=value.temporal_separation.total_seconds(),
        common_footprint=value.common_footprint,
        common_bbox=value.common_bbox,
        before_overlap_percent=value.before_overlap_percent,
        after_overlap_percent=value.after_overlap_percent,
        same_product=value.same_product,
        shared_polarizations=value.shared_polarizations,
        range_resolution_delta_percent=value.range_resolution_delta_percent,
        azimuth_resolution_delta_percent=value.azimuth_resolution_delta_percent,
        same_observation_direction=value.same_observation_direction,
        same_orbit_state=value.same_orbit_state,
        incidence_angle_delta_deg=value.incidence_angle_delta_deg,
        warnings=value.warnings,
    )


def _validate_source_identity(item: CatalogSearchItem) -> None:
    parsed = urlparse(item.source.href)
    expected_host = SOURCE_HOSTS[item.provider]
    if parsed.scheme != "https" or parsed.hostname != expected_host:
        raise AnalysisSelectionError(
            f"{item.provider} source identity must use its allowlisted HTTPS catalog host"
        )


def _model_sha256(value: BaseModel) -> str:
    return _sha256_json(value.model_dump(mode="json"))


def _sha256_json(value: Any) -> str:
    canonical = json.dumps(value, separators=(",", ":"), sort_keys=True).encode()
    return hashlib.sha256(canonical).hexdigest()


def _safe_runner_error(error: Exception) -> str:
    if isinstance(error, AnalysisProcessingError):
        return str(error)
    return "The deterministic preparation job failed. Review the configured inputs and retry."
