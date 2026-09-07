import json
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def test_production_requires_the_cli_release_path_for_prepared_assets() -> None:
    config = json.loads((REPOSITORY_ROOT / "vercel.json").read_text())
    ignore_rules = (REPOSITORY_ROOT / ".vercelignore").read_text().splitlines()

    assert config["git"]["deploymentEnabled"] is False
    assert "!api/**" in ignore_rules
    assert "!apps/**" in ignore_rules
    assert "!services/**" in ignore_rules
