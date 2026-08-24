from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel

from echoatlas import __version__


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: Literal["echoatlas-api"]
    version: str


def create_app() -> FastAPI:
    application = FastAPI(
        title="EchoAtlas API",
        summary="Local API foundation for the planned EchoAtlas analyst workbench.",
        version=__version__,
    )

    @application.get("/health", response_model=HealthResponse, tags=["system"])
    def health() -> HealthResponse:
        return HealthResponse(status="ok", service="echoatlas-api", version=__version__)

    return application


app = create_app()
