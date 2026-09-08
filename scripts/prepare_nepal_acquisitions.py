#!/usr/bin/env python3
"""Prepare bounded alternate Sentinel-2 views for the Nepal investigation."""

from __future__ import annotations

import json
from pathlib import Path

from echoatlas.nepal_imagery import NEPAL_WINDOW_END, NEPAL_WINDOW_START, NepalImageryService


def main() -> None:
    output_root = Path("apps/workbench/public/generated-nepal")
    image_root = output_root / "acquisitions"
    image_root.mkdir(parents=True, exist_ok=True)
    service = NepalImageryService()
    listing = service.list_acquisitions(NEPAL_WINDOW_START, NEPAL_WINDOW_END)
    payload = listing.model_dump(mode="json")
    for acquisition in payload["acquisitions"]:
        item_id = acquisition["item_id"]
        image_path = image_root / f"{item_id}.png"
        image_path.write_bytes(service.render_png(item_id))
        acquisition["image_url"] = f"/generated-nepal/acquisitions/{item_id}.png"
    (output_root / "acquisitions.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
