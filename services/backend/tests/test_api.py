from fastapi.testclient import TestClient

from echoatlas import __version__
from echoatlas.api.app import create_app


def test_health_reports_service_identity_and_version() -> None:
    response = TestClient(create_app()).get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "echoatlas-api",
        "version": __version__,
    }


def test_openapi_describes_only_the_foundation_route() -> None:
    response = TestClient(create_app()).get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["title"] == "EchoAtlas API"
    assert set(response.json()["paths"]) == {"/health"}
