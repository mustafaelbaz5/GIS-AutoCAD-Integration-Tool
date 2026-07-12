"""Loader for YAML column-mapping configuration files.

Column letters/names for the variable-schema secondary source (and,
for consistency, the base source) are never hard-coded in Python — they
are declared in YAML and loaded through this module.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class MappingConfigError(Exception):
    """Raised when a column-mapping YAML file is missing or malformed."""


@dataclass(frozen=True)
class MappingInfo:
    """Lightweight metadata about one available mapping file.

    Enough to populate a mapping-picker dropdown (Iteration 4 Task D)
    without fully validating the mapping's `fields`/`data_starts_at_row`
    — use `load_mapping` for that once a specific file is chosen.
    """

    path: Path
    name: str
    description: str


def load_mapping(path: Path) -> dict[str, Any]:
    """Load and minimally validate a column-mapping YAML file.

    Args:
        path: Path to the YAML mapping file.

    Returns:
        The parsed mapping as a dictionary, guaranteed to contain a
        "fields" section and a "data_starts_at_row" entry.

    Raises:
        MappingConfigError: If the file is missing or malformed.
    """
    if not path.exists():
        raise MappingConfigError(f"Mapping file not found: {path}")

    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)

    if not isinstance(data, dict):
        raise MappingConfigError(f"Mapping file must contain a YAML mapping: {path}")
    if "fields" not in data or not isinstance(data["fields"], dict):
        raise MappingConfigError(f"Mapping file missing a 'fields' section: {path}")
    if "data_starts_at_row" not in data:
        raise MappingConfigError(f"Mapping file missing 'data_starts_at_row': {path}")

    return data


def list_available_mappings(directory: Path) -> list[MappingInfo]:
    """List every column-mapping YAML file in `directory`, with its metadata.

    Malformed files (not a YAML mapping, or missing `name`/`description`)
    are skipped rather than raising — a broken file shouldn't prevent
    the picker from showing the other, valid mappings. `name` falls
    back to the filename stem and `description` to an empty string
    when absent, since those two fields are documentation, not
    structural requirements enforced by `load_mapping`.

    Args:
        directory: Directory to scan for `*.yaml` files, non-recursive.

    Returns:
        One `MappingInfo` per valid YAML file found, sorted by path.
    """
    mappings: list[MappingInfo] = []
    for path in sorted(directory.glob("*.yaml")):
        with path.open(encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
        if not isinstance(data, dict):
            continue
        mappings.append(
            MappingInfo(
                path=path,
                name=data.get("name", path.stem),
                description=data.get("description", ""),
            )
        )
    return mappings
