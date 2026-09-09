from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_yaml(relative_path: str | Path) -> dict[str, Any]:
    """Load a YAML file relative to the project root."""
    path = PROJECT_ROOT / relative_path
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_settings() -> dict[str, Any]:
    return load_yaml("config/settings.yaml")


def load_column_map() -> dict[str, str]:
    return load_yaml("config/column_map.yaml")


def project_path(path_value: str | Path) -> Path:
    return PROJECT_ROOT / path_value

