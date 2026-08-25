"""Project validated bundles into a deterministic, network-free Palantir import plan."""

from __future__ import annotations

import copy
import hashlib
from pathlib import Path
from typing import Literal, cast

from pydantic import BaseModel, ConfigDict, Field, model_validator

from echoatlas.bundle.validator import ValidatedBundle

OntologyObjectType = Literal[
    "AreaOfInterest",
    "Acquisition",
    "AnalysisRun",
    "EvidenceArtifact",
    "ChangeCandidate",
    "AnalystAssessment",
]
OntologyLinkType = Literal[
    "acquisitionCoversAoi",
    "runUsesAcquisition",
    "runProducesArtifact",
    "runProducesCandidate",
    "candidateAffectsAoi",
    "candidateReferencesArtifact",
    "assessmentAssessesCandidate",
    "assessmentReferencesArtifact",
    "assessmentSupersedesAssessment",
]

ONTOLOGY_LINK_TYPES: tuple[OntologyLinkType, ...] = (
    "acquisitionCoversAoi",
    "runUsesAcquisition",
    "runProducesArtifact",
    "runProducesCandidate",
    "candidateAffectsAoi",
    "candidateReferencesArtifact",
    "assessmentAssessesCandidate",
    "assessmentReferencesArtifact",
    "assessmentSupersedesAssessment",
)

ONTOLOGY_OBJECT_TYPES: tuple[OntologyObjectType, ...] = (
    "AreaOfInterest",
    "Acquisition",
    "AnalysisRun",
    "EvidenceArtifact",
    "ChangeCandidate",
    "AnalystAssessment",
)


class PalantirOntologyObject(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    object_type: OntologyObjectType
    primary_key: str = Field(min_length=1, max_length=1000)
    properties: dict[str, object]


class PalantirOntologyLink(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    link_type: OntologyLinkType
    source_type: OntologyObjectType
    source_primary_key: str = Field(min_length=1, max_length=1000)
    target_type: OntologyObjectType
    target_primary_key: str = Field(min_length=1, max_length=1000)


class PalantirMediaUpload(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    artifact_primary_key: str = Field(min_length=1, max_length=1000)
    source_relative_path: str = Field(min_length=1, max_length=1000)
    media_type: str = Field(pattern=r"^[a-z0-9.+-]+/[a-z0-9.+-]+$")
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    size_bytes: int = Field(gt=0)


class PalantirImportPlan(BaseModel):
    """Portable projection only; this contract performs no Palantir writes."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    import_plan_version: Literal["1.0.0"] = "1.0.0"
    source_bundle_id: str = Field(min_length=1, max_length=200)
    source_manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    ontology_object_types: tuple[OntologyObjectType, ...] = ONTOLOGY_OBJECT_TYPES
    objects: tuple[PalantirOntologyObject, ...]
    links: tuple[PalantirOntologyLink, ...]
    media_uploads: tuple[PalantirMediaUpload, ...]
    requires_authenticated_target: Literal[True] = True
    writes_performed: Literal[False] = False
    policy_boundaries: tuple[str, ...]
    warnings: tuple[str, ...]

    @model_validator(mode="after")
    def validate_references(self) -> PalantirImportPlan:
        identities = {(item.object_type, item.primary_key) for item in self.objects}
        if len(identities) != len(self.objects):
            raise ValueError("ontology object identities must be unique")
        for link in self.links:
            source = (link.source_type, link.source_primary_key)
            target = (link.target_type, link.target_primary_key)
            if source not in identities or target not in identities:
                raise ValueError("ontology links must reference objects in the import plan")
        artifact_keys = {
            item.primary_key for item in self.objects if item.object_type == "EvidenceArtifact"
        }
        if any(item.artifact_primary_key not in artifact_keys for item in self.media_uploads):
            raise ValueError("media uploads must reference evidence artifacts in the import plan")
        return self


def plan_palantir_import(bundle: ValidatedBundle) -> PalantirImportPlan:
    """Map a validated provider-neutral bundle without calling Palantir services."""

    manifest = bundle.manifest
    components = bundle.components
    bundle_id = cast(str, manifest["bundle_id"])
    source_processing_run_id = cast(str, manifest["source_processing_run_id"])
    change_run_id = cast(str, manifest["change_run_id"])
    manifest_sha256 = _sha256(bundle.root / "manifest.json")

    aoi = components["aoi"]
    aoi_properties = cast(dict[str, object], aoi["properties"])
    aoi_key = cast(str, aoi_properties["aoi_id"])
    run_key = f"{source_processing_run_id}:{manifest_sha256}"

    objects: list[PalantirOntologyObject] = [
        PalantirOntologyObject(
            object_type="AreaOfInterest",
            primary_key=aoi_key,
            properties={
                **_copy(aoi_properties),
                "geometry": _copy(cast(dict[str, object], aoi["geometry"])),
                "source_bundle_id": bundle_id,
            },
        )
    ]
    links: list[PalantirOntologyLink] = []

    acquisition_keys: list[str] = []
    acquisitions = cast(list[dict[str, object]], components["acquisitions"]["acquisitions"])
    for acquisition in acquisitions:
        acquisition_key = f"{acquisition['provider']}:{acquisition['source_item_id']}"
        acquisition_keys.append(acquisition_key)
        objects.append(
            PalantirOntologyObject(
                object_type="Acquisition",
                primary_key=acquisition_key,
                properties={**_copy(acquisition), "source_bundle_id": bundle_id},
            )
        )
        links.append(
            _link(
                "acquisitionCoversAoi",
                "Acquisition",
                acquisition_key,
                "AreaOfInterest",
                aoi_key,
            )
        )

    objects.append(
        PalantirOntologyObject(
            object_type="AnalysisRun",
            primary_key=run_key,
            properties={
                "source_bundle_id": bundle_id,
                "source_processing_run_id": source_processing_run_id,
                "change_run_id": change_run_id,
                "source_manifest_sha256": manifest_sha256,
                "status": manifest["status"],
                "created_at": manifest["created_at"],
                "software": _copy(cast(dict[str, object], manifest["software"])),
                "parameters": _copy(cast(dict[str, object], manifest["parameters"])),
                "warnings": _copy(cast(list[object], manifest["warnings"])),
            },
        )
    )
    for acquisition_key in acquisition_keys:
        links.append(
            _link(
                "runUsesAcquisition",
                "AnalysisRun",
                run_key,
                "Acquisition",
                acquisition_key,
            )
        )

    artifact_keys: dict[str, str] = {}
    media_uploads: list[PalantirMediaUpload] = []
    artifacts = sorted(
        cast(list[dict[str, object]], manifest["artifacts"]),
        key=lambda item: cast(str, item["artifact_id"]),
    )
    for artifact in artifacts:
        artifact_id = cast(str, artifact["artifact_id"])
        artifact_key = f"{bundle_id}:{artifact_id}:{artifact['sha256']}"
        artifact_keys[artifact_id] = artifact_key
        objects.append(
            PalantirOntologyObject(
                object_type="EvidenceArtifact",
                primary_key=artifact_key,
                properties={**_copy(artifact), "source_bundle_id": bundle_id},
            )
        )
        links.append(
            _link(
                "runProducesArtifact",
                "AnalysisRun",
                run_key,
                "EvidenceArtifact",
                artifact_key,
            )
        )
        if artifact["status"] == "available":
            media_uploads.append(
                PalantirMediaUpload(
                    artifact_primary_key=artifact_key,
                    source_relative_path=cast(str, artifact["path"]),
                    media_type=cast(str, artifact["media_type"]),
                    sha256=cast(str, artifact["sha256"]),
                    size_bytes=cast(int, artifact["size_bytes"]),
                )
            )

    candidate_keys: dict[str, str] = {}
    features = sorted(
        cast(list[dict[str, object]], components["candidates"]["features"]),
        key=lambda item: cast(str, item["id"]),
    )
    for feature in features:
        properties = cast(dict[str, object], feature["properties"])
        candidate_id = cast(str, properties["candidate_id"])
        candidate_key = f"{change_run_id}:{candidate_id}"
        candidate_keys[candidate_id] = candidate_key
        objects.append(
            PalantirOntologyObject(
                object_type="ChangeCandidate",
                primary_key=candidate_key,
                properties={
                    **_copy(properties),
                    "geometry": _copy(cast(dict[str, object], feature["geometry"])),
                    "source_bundle_id": bundle_id,
                },
            )
        )
        links.extend(
            (
                _link(
                    "runProducesCandidate",
                    "AnalysisRun",
                    run_key,
                    "ChangeCandidate",
                    candidate_key,
                ),
                _link(
                    "candidateAffectsAoi",
                    "ChangeCandidate",
                    candidate_key,
                    "AreaOfInterest",
                    aoi_key,
                ),
            )
        )
        for artifact_id in cast(list[str], properties["evidence_artifact_ids"]):
            links.append(
                _link(
                    "candidateReferencesArtifact",
                    "ChangeCandidate",
                    candidate_key,
                    "EvidenceArtifact",
                    artifact_keys[artifact_id],
                )
            )

    assessment_keys: dict[str, str] = {}
    events = cast(list[dict[str, object]], components["assessments"]["events"])
    for event in events:
        assessment_id = cast(str, event["assessment_id"])
        assessment_key = f"{bundle_id}:{assessment_id}"
        assessment_keys[assessment_id] = assessment_key
        objects.append(
            PalantirOntologyObject(
                object_type="AnalystAssessment",
                primary_key=assessment_key,
                properties={**_copy(event), "source_bundle_id": bundle_id},
            )
        )
        candidate_id = cast(str, event["candidate_id"])
        links.append(
            _link(
                "assessmentAssessesCandidate",
                "AnalystAssessment",
                assessment_key,
                "ChangeCandidate",
                candidate_keys[candidate_id],
            )
        )
        for artifact_id in cast(list[str], event["evidence_artifact_ids"]):
            links.append(
                _link(
                    "assessmentReferencesArtifact",
                    "AnalystAssessment",
                    assessment_key,
                    "EvidenceArtifact",
                    artifact_keys[artifact_id],
                )
            )
        supersedes = event.get("supersedes_assessment_id")
        if isinstance(supersedes, str):
            links.append(
                _link(
                    "assessmentSupersedesAssessment",
                    "AnalystAssessment",
                    assessment_key,
                    "AnalystAssessment",
                    assessment_keys[supersedes],
                )
            )

    warnings = [
        "This plan is a local projection and has not authenticated to or written into Palantir.",
        "PNG preview artifacts are media items, not raster-native GeoTIFF layers.",
        "Developer Tier quotas and enabled products must be verified in the target enrollment.",
    ]
    if bundle.missing_artifact_ids:
        warnings.append(
            "Missing artifacts remain represented as metadata but are excluded from media uploads."
        )

    return PalantirImportPlan(
        source_bundle_id=bundle_id,
        source_manifest_sha256=manifest_sha256,
        objects=tuple(objects),
        links=tuple(links),
        media_uploads=tuple(media_uploads),
        policy_boundaries=(
            "EchoAtlas remains the system of record for deterministic SAR processing policy.",
            "Palantir receives validated bundle outputs only; "
            "it does not redefine candidate logic.",
            "No assessment, alert, AI inference, or external action is created by this projection.",
        ),
        warnings=tuple(warnings),
    )


def _link(
    link_type: OntologyLinkType,
    source_type: OntologyObjectType,
    source_primary_key: str,
    target_type: OntologyObjectType,
    target_primary_key: str,
) -> PalantirOntologyLink:
    return PalantirOntologyLink(
        link_type=link_type,
        source_type=source_type,
        source_primary_key=source_primary_key,
        target_type=target_type,
        target_primary_key=target_primary_key,
    )


def _copy[T](value: T) -> T:
    return copy.deepcopy(value)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
