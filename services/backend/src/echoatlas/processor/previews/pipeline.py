"""Validated common-grid alignment and display-only SAR preview generation."""

from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
from pathlib import Path
from typing import Literal, cast
from uuid import uuid4

import numpy as np
import numpy.typing as npt
import rasterio  # type: ignore[import-untyped]
from affine import Affine
from PIL import Image
from PIL import __version__ as pillow_version
from rasterio.crs import CRS  # type: ignore[import-untyped]
from rasterio.enums import ColorInterp, Resampling  # type: ignore[import-untyped]
from rasterio.errors import RasterioIOError  # type: ignore[import-untyped]
from rasterio.features import geometry_mask  # type: ignore[import-untyped]
from rasterio.io import DatasetReader  # type: ignore[import-untyped]
from rasterio.transform import from_origin  # type: ignore[import-untyped]
from rasterio.warp import (  # type: ignore[import-untyped]
    reproject,
    transform_bounds,
    transform_geom,
)

from echoatlas import __version__
from echoatlas.processor.acquisition.models import SelectionManifest
from echoatlas.processor.previews.models import (
    ArtifactRecord,
    GridRecord,
    ProcessingParameters,
    ProcessingResult,
    ProcessingRunManifest,
    QualityReport,
    RasterSourceRecord,
    RoleQualityRecord,
)

_MAX_SOURCE_DIMENSION = 100_000
_MAX_SOURCE_PIXELS = 1_000_000_000


class PreviewProcessingError(RuntimeError):
    """Base class for deterministic preview processing failures."""


class RasterValidationError(PreviewProcessingError):
    """A source raster is corrupt, incompatible, or incomplete."""


class OutputExistsError(PreviewProcessingError):
    """A deterministic run output already exists and is immutable."""


def process_pair(
    manifest: SelectionManifest,
    sources: dict[str, Path],
    *,
    output_root: Path,
    parameters: ProcessingParameters | None = None,
) -> ProcessingResult:
    config = parameters or ProcessingParameters()
    if set(sources) != {"before", "after"}:
        raise RasterValidationError("processing requires exactly before and after source paths")

    grid, aoi_mask = _build_grid(manifest, config)
    run_id = _run_id(manifest, config)
    final_directory = output_root / run_id
    if final_directory.exists():
        raise OutputExistsError(f"processing output already exists: {final_directory}")

    output_root.mkdir(parents=True, exist_ok=True)
    working_directory = output_root / f".{run_id}.{uuid4().hex}.tmp"
    try:
        working_directory.mkdir()
        artifacts: list[ArtifactRecord] = []
        source_records: list[RasterSourceRecord] = []
        quality_records: list[RoleQualityRecord] = []
        valid_masks: list[npt.NDArray[np.bool_]] = []

        for role in ("before", "after"):
            source_record, quality_record, role_artifacts, valid_mask = _process_role(
                role,
                manifest,
                sources[role],
                working_directory,
                grid,
                aoi_mask,
                config,
            )
            source_records.append(source_record)
            quality_records.append(quality_record)
            artifacts.extend(role_artifacts)
            valid_masks.append(valid_mask)

        common_valid = valid_masks[0] & valid_masks[1]
        common_count = int(np.count_nonzero(common_valid))
        common_fraction = common_count / grid.aoi_pixel_count
        warnings = _quality_warnings(config, source_records)
        quality_report = QualityReport(
            run_id=run_id,
            selection_id=manifest.selection_id,
            grid=grid,
            sources=cast(tuple[RasterSourceRecord, RasterSourceRecord], tuple(source_records)),
            roles=cast(tuple[RoleQualityRecord, RoleQualityRecord], tuple(quality_records)),
            common_valid_pixel_count=common_count,
            common_valid_fraction=common_fraction,
            warnings=warnings,
        )
        quality_path = working_directory / "quality-report.json"
        _write_json(quality_path, quality_report.model_dump(mode="json"))

        run_manifest = ProcessingRunManifest(
            run_id=run_id,
            selection_id=manifest.selection_id,
            processing_aoi_id=manifest.processing_aoi.id,
            processing_aoi_geometry_sha256=manifest.processing_aoi.geometry_sha256,
            source_license=manifest.license.model_dump(mode="json"),
            inputs=cast(
                tuple[dict[str, object], dict[str, object]],
                tuple(
                    {
                        "role": role,
                        "item_id": manifest.acquisitions[role].item_id,
                        "file_name": sources[role].name,
                        "source_url": manifest.acquisitions[role].object.url,
                        "source_key": manifest.acquisitions[role].object.key,
                        "size_bytes": manifest.acquisitions[role].object.size_bytes,
                        "etag": manifest.acquisitions[role].object.etag,
                        "checksum": manifest.acquisitions[role].object.checksum.model_dump(
                            mode="json"
                        ),
                    }
                    for role in ("before", "after")
                ),
            ),
            parameters=config,
            grid=grid,
            software={
                "echoatlas": __version__,
                "numpy": np.__version__,
                "rasterio": rasterio.__version__,
                "gdal": rasterio.__gdal_version__,
                "pillow": pillow_version,
            },
            artifacts=tuple(artifacts),
            quality_report={
                "relative_path": "quality-report.json",
                "sha256": _sha256_file(quality_path),
                "size_bytes": quality_path.stat().st_size,
            },
            interpretation_limits=manifest.interpretation_limits,
            sensitivity_controls=manifest.sensitivity_controls,
        )
        manifest_path = working_directory / "processing-manifest.json"
        _write_json(manifest_path, run_manifest.model_dump(mode="json"))

        os.rename(working_directory, final_directory)
    except Exception:
        shutil.rmtree(working_directory, ignore_errors=True)
        raise

    return ProcessingResult(
        run_id=run_id,
        output_directory=final_directory,
        manifest_path=final_directory / "processing-manifest.json",
        quality_report_path=final_directory / "quality-report.json",
        artifacts=tuple(artifacts),
    )


def _build_grid(
    manifest: SelectionManifest, parameters: ProcessingParameters
) -> tuple[GridRecord, npt.NDArray[np.bool_]]:
    target_crs = CRS.from_string(parameters.target_crs)
    west, south, east, north = transform_bounds(
        "EPSG:4326",
        target_crs,
        *manifest.processing_aoi.bbox,
        densify_pts=21,
    )
    resolution = parameters.target_resolution
    left = math.floor(west / resolution) * resolution
    bottom = math.floor(south / resolution) * resolution
    right = math.ceil(east / resolution) * resolution
    top = math.ceil(north / resolution) * resolution
    width = int(round((right - left) / resolution))
    height = int(round((top - bottom) / resolution))
    if width <= 0 or height <= 0 or width * height > _MAX_SOURCE_PIXELS:
        raise RasterValidationError("declared processing grid is empty or exceeds pixel limit")
    transform = from_origin(left, top, resolution, resolution)
    projected_geometry = transform_geom(
        "EPSG:4326",
        target_crs,
        manifest.processing_aoi.geometry,
        precision=9,
    )
    aoi_mask = geometry_mask(
        [projected_geometry],
        out_shape=(height, width),
        transform=transform,
        invert=True,
        all_touched=False,
    )
    aoi_pixel_count = int(np.count_nonzero(aoi_mask))
    if aoi_pixel_count == 0:
        raise RasterValidationError("processing AOI contains no target pixels")
    return (
        GridRecord(
            crs=target_crs.to_string(),
            resolution=resolution,
            width=width,
            height=height,
            bounds=(left, bottom, right, top),
            transform=cast(
                tuple[float, float, float, float, float, float, float, float, float],
                tuple(transform),
            ),
            aoi_pixel_count=aoi_pixel_count,
        ),
        aoi_mask,
    )


def _process_role(
    role: Literal["before", "after"],
    manifest: SelectionManifest,
    source_path: Path,
    output_directory: Path,
    grid: GridRecord,
    aoi_mask: npt.NDArray[np.bool_],
    parameters: ProcessingParameters,
) -> tuple[
    RasterSourceRecord,
    RoleQualityRecord,
    tuple[ArtifactRecord, ArtifactRecord, ArtifactRecord],
    npt.NDArray[np.bool_],
]:
    try:
        with rasterio.open(source_path) as source:
            source_record = _validate_source(
                role, manifest.acquisitions[role].item_id, source_path, source, manifest
            )
            aligned = np.full((grid.height, grid.width), np.nan, dtype=np.float32)
            reproject(
                source=rasterio.band(source, 1),
                destination=aligned,
                src_transform=source.transform,
                src_crs=source.crs,
                src_nodata=source.nodata,
                dst_transform=Affine(*grid.transform[:6]),
                dst_crs=grid.crs,
                dst_nodata=np.nan,
                resampling=Resampling.bilinear,
                init_dest_nodata=True,
                num_threads=2,
            )
    except RasterioIOError as error:
        raise RasterValidationError(f"{role} raster could not be opened: {error}") from error

    aligned[~aoi_mask] = np.nan
    valid_mask = np.isfinite(aligned) & aoi_mask
    valid_count = int(np.count_nonzero(valid_mask))
    valid_fraction = valid_count / grid.aoi_pixel_count
    if valid_fraction < parameters.min_valid_fraction:
        raise RasterValidationError(
            f"{role} raster valid AOI coverage {valid_fraction:.6f} is below "
            f"{parameters.min_valid_fraction:.6f}"
        )
    valid_values = aligned[valid_mask]
    lower, upper = (
        float(value)
        for value in np.percentile(
            valid_values, [parameters.lower_percentile, parameters.upper_percentile]
        )
    )
    if not math.isfinite(lower) or not math.isfinite(upper) or lower >= upper:
        raise RasterValidationError(f"{role} raster has no usable normalization range")

    aligned_path = output_directory / "aligned" / f"{role}.tif"
    preview_path = output_directory / "previews" / f"{role}.png"
    thumbnail_path = output_directory / "thumbnails" / f"{role}.png"
    _write_aligned(aligned_path, aligned, valid_mask, grid, role, manifest.selection_id)
    preview = _normalize_preview(aligned, valid_mask, lower, upper)
    _write_preview(preview_path, thumbnail_path, preview, parameters.thumbnail_max_size)

    quality = RoleQualityRecord(
        role=role,
        valid_pixel_count=valid_count,
        aoi_pixel_count=grid.aoi_pixel_count,
        valid_fraction=valid_fraction,
        value_min=float(valid_values.min()),
        value_max=float(valid_values.max()),
        normalization_low=lower,
        normalization_high=upper,
    )
    with Image.open(thumbnail_path) as thumbnail_image:
        thumbnail_width, thumbnail_height = thumbnail_image.size
    artifacts = (
        _artifact(role, "aligned-raster", aligned_path, output_directory, grid.width, grid.height),
        _artifact(role, "preview", preview_path, output_directory, grid.width, grid.height),
        _artifact(
            role,
            "thumbnail",
            thumbnail_path,
            output_directory,
            thumbnail_width,
            thumbnail_height,
        ),
    )
    return source_record, quality, artifacts, valid_mask


def _validate_source(
    role: Literal["before", "after"],
    item_id: str,
    source_path: Path,
    source: DatasetReader,
    manifest: SelectionManifest,
) -> RasterSourceRecord:
    if source.driver != "GTiff":
        raise RasterValidationError(f"{role} raster driver must be GTiff")
    if source.crs is None:
        raise RasterValidationError(f"{role} raster is missing a CRS")
    if source.count != 1:
        raise RasterValidationError(f"{role} raster must contain exactly one band")
    dtype = np.dtype(source.dtypes[0])
    if not np.issubdtype(dtype, np.number) or np.issubdtype(dtype, np.complexfloating):
        raise RasterValidationError(f"{role} raster dtype is not supported: {dtype}")
    if source.nodata is None:
        raise RasterValidationError(f"{role} raster must declare nodata")
    if source.width > _MAX_SOURCE_DIMENSION or source.height > _MAX_SOURCE_DIMENSION:
        raise RasterValidationError(f"{role} raster dimensions exceed the safety limit")
    if source.width * source.height > _MAX_SOURCE_PIXELS:
        raise RasterValidationError(f"{role} raster pixel count exceeds the safety limit")
    transform_values = tuple(source.transform)
    if not all(math.isfinite(value) for value in transform_values):
        raise RasterValidationError(f"{role} raster transform contains non-finite values")
    if abs(source.transform.determinant) <= 1e-18:
        raise RasterValidationError(f"{role} raster transform is not invertible")
    color_interpretation = source.colorinterp[0]
    if color_interpretation not in {ColorInterp.gray, ColorInterp.undefined}:
        raise RasterValidationError(f"{role} raster band is not grayscale")

    try:
        wgs84_bounds = transform_bounds(source.crs, "EPSG:4326", *source.bounds, densify_pts=21)
    except Exception as error:
        raise RasterValidationError(f"{role} raster bounds could not be transformed") from error
    west, south, east, north = manifest.processing_aoi.bbox
    if (
        wgs84_bounds[2] <= west
        or wgs84_bounds[0] >= east
        or wgs84_bounds[3] <= south
        or wgs84_bounds[1] >= north
    ):
        raise RasterValidationError(f"{role} raster does not intersect the processing AOI")

    return RasterSourceRecord(
        role=role,
        item_id=item_id,
        file_name=source_path.name,
        driver=source.driver,
        crs=source.crs.to_string(),
        dtype=source.dtypes[0],
        width=source.width,
        height=source.height,
        count=1,
        transform=cast(
            tuple[float, float, float, float, float, float, float, float, float],
            transform_values,
        ),
        resolution=(float(source.res[0]), float(source.res[1])),
        bounds=cast(
            tuple[float, float, float, float],
            tuple(float(value) for value in source.bounds),
        ),
        wgs84_bounds=cast(
            tuple[float, float, float, float],
            tuple(float(value) for value in wgs84_bounds),
        ),
        nodata=float(source.nodata),
        color_interpretation=color_interpretation.name,
        rotated_transform=not math.isclose(source.transform.b, 0.0)
        or not math.isclose(source.transform.d, 0.0),
    )


def _write_aligned(
    path: Path,
    aligned: npt.NDArray[np.float32],
    valid_mask: npt.NDArray[np.bool_],
    grid: GridRecord,
    role: str,
    selection_id: str,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        width=grid.width,
        height=grid.height,
        count=1,
        dtype="float32",
        crs=grid.crs,
        transform=Affine(*grid.transform[:6]),
        nodata=np.nan,
        compress="deflate",
        predictor=3,
        tiled=True,
        blockxsize=256,
        blockysize=256,
    ) as destination:
        destination.write(aligned, 1)
        destination.write_mask(valid_mask.astype(np.uint8) * 255)
        destination.update_tags(
            ECHOATLAS_SELECTION_ID=selection_id,
            ECHOATLAS_ROLE=role,
            ECHOATLAS_PRODUCT="aligned-source-intensity",
        )


def _normalize_preview(
    aligned: npt.NDArray[np.float32],
    valid_mask: npt.NDArray[np.bool_],
    lower: float,
    upper: float,
) -> npt.NDArray[np.uint8]:
    preview = np.zeros(aligned.shape, dtype=np.uint8)
    scaled = (np.clip(aligned[valid_mask], lower, upper) - lower) / (upper - lower)
    preview[valid_mask] = np.rint(scaled * 254 + 1).astype(np.uint8)
    return preview


def _write_preview(
    preview_path: Path,
    thumbnail_path: Path,
    preview: npt.NDArray[np.uint8],
    thumbnail_max_size: int,
) -> None:
    preview_path.parent.mkdir(parents=True, exist_ok=True)
    thumbnail_path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.fromarray(preview)
    image.save(preview_path, format="PNG", compress_level=9, optimize=False)
    thumbnail = image.copy()
    thumbnail.thumbnail(
        (thumbnail_max_size, thumbnail_max_size),
        resample=Image.Resampling.LANCZOS,
        reducing_gap=3.0,
    )
    thumbnail.save(thumbnail_path, format="PNG", compress_level=9, optimize=False)


def _artifact(
    role: Literal["before", "after"],
    kind: Literal["aligned-raster", "preview", "thumbnail"],
    path: Path,
    output_directory: Path,
    width: int,
    height: int,
) -> ArtifactRecord:
    media_type = "image/tiff" if kind == "aligned-raster" else "image/png"
    return ArtifactRecord(
        artifact_id=f"{role}-{kind}",
        role=role,
        kind=kind,
        relative_path=path.relative_to(output_directory).as_posix(),
        media_type=media_type,
        sha256=_sha256_file(path),
        size_bytes=path.stat().st_size,
        width=width,
        height=height,
    )


def _quality_warnings(
    parameters: ProcessingParameters, sources: list[RasterSourceRecord]
) -> tuple[str, ...]:
    warnings = [
        "Independent percentile stretches are display normalization, not calibrated "
        "backscatter normalization.",
        "Bilinear resampling changes pixel values and can smooth high-frequency SAR texture.",
        "No speckle filter is applied; apparent differences may include speckle and "
        "acquisition-geometry effects.",
        "Aligned previews are engineering artifacts and do not establish change, cause, "
        "damage, or confidence.",
    ]
    if any(source.rotated_transform for source in sources):
        warnings.append(
            "At least one source has a rotated affine transform and was reprojected to "
            "the north-up target grid."
        )
    if parameters.target_resolution > 0.5:
        warnings.append(
            "The 1-meter target grid is coarser than the declared approximately "
            "0.5-meter source resolution."
        )
    return tuple(warnings)


def _run_id(manifest: SelectionManifest, parameters: ProcessingParameters) -> str:
    identity = {
        "selection_id": manifest.selection_id,
        "aoi_geometry_sha256": manifest.processing_aoi.geometry_sha256,
        "inputs": {
            role: manifest.acquisitions[role].object.checksum.model_dump(mode="json")
            for role in ("before", "after")
        },
        "parameters": parameters.model_dump(mode="json"),
    }
    digest = hashlib.sha256(
        json.dumps(identity, separators=(",", ":"), sort_keys=True).encode()
    ).hexdigest()
    return f"preview-{digest[:20]}"


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(f"{json.dumps(payload, indent=2, sort_keys=True)}\n", encoding="utf-8")


def _sha256_file(path: Path) -> str:
    checksum = hashlib.sha256()
    with path.open("rb") as handle:
        while payload := handle.read(1024 * 1024):
            checksum.update(payload)
    return checksum.hexdigest()
