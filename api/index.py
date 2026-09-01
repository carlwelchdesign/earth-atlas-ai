"""Vercel entrypoint for EchoAtlas's bounded public metadata API."""

from __future__ import annotations

import os
import sys
from collections.abc import Mapping
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "backend" / "src"))


def _prepared_bundle_path(root: Path, environment: Mapping[str, str]) -> Path:
    asset_root = "dist" if environment.get("VERCEL") == "1" else "public"
    return root / "apps" / "workbench" / asset_root / "generated-demo" / "bundle.json"


os.environ.setdefault(
    "ECHOATLAS_PREPARED_BUNDLE_PATH",
    str(_prepared_bundle_path(ROOT, os.environ)),
)
os.environ.setdefault("ECHOATLAS_ANALYSIS_RUN_INLINE", "1")

from fastapi import FastAPI  # noqa: E402

from echoatlas.api.app import create_app  # noqa: E402
from echoatlas.processor.catalog.providers import (  # noqa: E402
    build_default_catalog_search_service,
)

PUBLIC_UMBRA_ITEM_URLS = (
    "https://umbra-open-data-catalog.s3.us-west-2.amazonaws.com/stac/2025/2025-06/"
    "2025-06-10/89284e7a-04bc-4917-9467-502f2ff3bece/"
    "89284e7a-04bc-4917-9467-502f2ff3bece.json",
    "https://umbra-open-data-catalog.s3.us-west-2.amazonaws.com/stac/2025/2025-07/"
    "2025-07-05/f784904e-b115-4a2c-b5d5-9a94ed075e94/"
    "f784904e-b115-4a2c-b5d5-9a94ed075e94.json",
)

app = FastAPI(
    title="EchoAtlas public portfolio API",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)
app.mount(
    "/api",
    create_app(
        catalog_search=build_default_catalog_search_service(umbra_item_urls=PUBLIC_UMBRA_ITEM_URLS)
    ),
)
