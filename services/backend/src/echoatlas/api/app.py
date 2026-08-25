from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from echoatlas import __version__
from echoatlas.processor.catalog.providers import build_default_catalog_search_service
from echoatlas.processor.catalog.search import CatalogSearchError, CatalogSearchService
from echoatlas.processor.catalog.search_models import CatalogSearchRequest, CatalogSearchResponse


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: Literal["echoatlas-api"]
    version: str


def create_app(catalog_search: CatalogSearchService | None = None) -> FastAPI:
    search_service = catalog_search or build_default_catalog_search_service()
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

    return application


app = create_app()
