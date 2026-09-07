from typing import Literal

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

from echoatlas import __version__
from echoatlas.analysis_jobs import (
    AnalysisJobCreateRequest,
    AnalysisJobError,
    AnalysisJobRetryRequest,
    AnalysisJobService,
    AnalysisJobView,
    AnalysisSelectionError,
    AnalysisSelectionManifest,
    AnalysisSelectionRequest,
    build_default_analysis_job_service,
    create_selection_manifest,
)
from echoatlas.places import (
    PlaceSearchError,
    PlaceSearchRequest,
    PlaceSearchResponse,
    PlaceSearchService,
    build_default_place_search_service,
)
from echoatlas.processor.catalog.providers import build_default_catalog_search_service
from echoatlas.processor.catalog.search import CatalogSearchError, CatalogSearchService
from echoatlas.processor.catalog.search_models import CatalogSearchRequest, CatalogSearchResponse


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: Literal["echoatlas-api"]
    version: str


def create_app(
    catalog_search: CatalogSearchService | None = None,
    place_search: PlaceSearchService | None = None,
    analysis_jobs: AnalysisJobService | None = None,
) -> FastAPI:
    search_service = catalog_search or build_default_catalog_search_service()
    place_service = place_search or build_default_place_search_service()
    analysis_service = analysis_jobs or build_default_analysis_job_service()
    application = FastAPI(
        title="EchoAtlas API",
        summary="Local API foundation for the planned EchoAtlas analyst workbench.",
        version=__version__,
    )

    @application.get("/health", response_model=HealthResponse, tags=["system"])
    def health() -> HealthResponse:
        return HealthResponse(status="ok", service="echoatlas-api", version=__version__)

    @application.post(
        "/v1/catalog/search",
        response_model=CatalogSearchResponse,
        tags=["catalog"],
        summary="Search bounded provider-reported SAR acquisition metadata",
    )
    def search_catalog(request: CatalogSearchRequest) -> CatalogSearchResponse:
        try:
            return search_service.search(request)
        except CatalogSearchError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    @application.post(
        "/v1/places/resolve",
        response_model=PlaceSearchResponse,
        tags=["places"],
        summary="Resolve one explicit place query to a bounded Explore AOI",
    )
    def resolve_place(request: PlaceSearchRequest) -> PlaceSearchResponse:
        try:
            return place_service.resolve(request.query)
        except PlaceSearchError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    @application.post(
        "/v1/analysis/selections",
        response_model=AnalysisSelectionManifest,
        tags=["analysis"],
        summary="Create an immutable manifest with deterministic pair-comparability evidence",
    )
    def create_analysis_selection(
        request: AnalysisSelectionRequest,
    ) -> AnalysisSelectionManifest:
        try:
            return create_selection_manifest(request)
        except AnalysisSelectionError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

    @application.post(
        "/v1/analysis/jobs",
        response_model=AnalysisJobView,
        status_code=status.HTTP_202_ACCEPTED,
        tags=["analysis"],
        summary="Queue a bounded deterministic preparation job",
    )
    def create_analysis_job(request: AnalysisJobCreateRequest) -> AnalysisJobView:
        try:
            return analysis_service.create(request.manifest)
        except AnalysisJobError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error

    @application.get(
        "/v1/analysis/jobs/{job_id}",
        response_model=AnalysisJobView,
        tags=["analysis"],
        summary="Read one preparation job state",
    )
    def get_analysis_job(job_id: str) -> AnalysisJobView:
        try:
            return analysis_service.get(job_id)
        except AnalysisJobError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    @application.delete(
        "/v1/analysis/jobs/{job_id}",
        response_model=AnalysisJobView,
        tags=["analysis"],
        summary="Cancel one queued or running preparation job",
    )
    def cancel_analysis_job(job_id: str) -> AnalysisJobView:
        try:
            return analysis_service.cancel(job_id)
        except AnalysisJobError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error

    @application.post(
        "/v1/analysis/jobs/{job_id}/retry",
        response_model=AnalysisJobView,
        status_code=status.HTTP_202_ACCEPTED,
        tags=["analysis"],
        summary="Retry a failed or cancelled preparation job",
    )
    def retry_analysis_job(job_id: str, request: AnalysisJobRetryRequest) -> AnalysisJobView:
        try:
            return analysis_service.retry(job_id, request.manifest_sha256)
        except AnalysisJobError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error

    return application


app = create_app()
