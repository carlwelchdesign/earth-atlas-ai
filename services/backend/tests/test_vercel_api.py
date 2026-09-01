from pathlib import Path

from fastapi.testclient import TestClient

from api.index import _prepared_bundle_path, app


def test_vercel_runtime_reads_the_built_static_bundle() -> None:
    root = Path("/project")

    assert _prepared_bundle_path(root, {"VERCEL": "1"}) == (
        root / "apps/workbench/dist/generated-demo/bundle.json"
    )
    assert _prepared_bundle_path(root, {}) == (
        root / "apps/workbench/public/generated-demo/bundle.json"
    )


def test_vercel_api_mount_exposes_the_bounded_backend() -> None:
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "echoatlas-api",
        "version": "0.1.0",
    }


def test_vercel_api_mount_does_not_expose_a_root_api() -> None:
    response = TestClient(app).get("/health")

    assert response.status_code == 404
