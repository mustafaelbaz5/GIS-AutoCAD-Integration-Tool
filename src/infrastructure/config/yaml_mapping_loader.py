"""Loader for YAML column-mapping configuration files.

Column letters/names for the variable-schema secondary source (and,
for consistency, the base source) are never hard-coded in Python — they
are declared in YAML and loaded through this module.
"""

from pathlib import Path
from typing import Any

import yaml


class MappingConfigError(Exception):
    """Raised when a column-mapping YAML file is missing or malformed."""


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
