"""Headless pipeline runner: base file + secondary file -> merged Excel output.

Usage:
    python scripts/cli_run.py <base_file> <secondary_file> [output_path]
        [--base-mapping PATH] [--secondary-mapping PATH] [--no-sort]

Proves the full pipeline (read -> merge -> spatial sort -> write) works
end-to-end before the GUI is wired up, per project brief Phase 5.
"""

import argparse
import sys
import time
from pathlib import Path

from loguru import logger
from src.application.use_cases.export_final_file_use_case import ExportFinalFileUseCase
from src.application.use_cases.merge_parcels_use_case import MergeParcelsUseCase
from src.domain.services.spatial_sorter import SpatialSorter
from src.infrastructure.config.default_landmarks import DEFAULT_LANDMARK_KEYWORDS
from src.infrastructure.config.yaml_mapping_loader import load_mapping
from src.infrastructure.excel.base_file_reader import BaseFileReader
from src.infrastructure.excel.professional_excel_writer import (
    ProfessionalExcelWriter,
    default_output_filename,
)
from src.infrastructure.excel.secondary_file_reader import SecondaryFileReader
from src.infrastructure.excel.yaml_column_mapper import YamlColumnMapper
from src.infrastructure.logging_setup import configure_logging

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_MAPPINGS_DIR = _PROJECT_ROOT / "src" / "infrastructure" / "config" / "default_mappings"
_DEFAULT_BASE_MAPPING = _DEFAULT_MAPPINGS_DIR / "system_file_default.yaml"
_DEFAULT_SECONDARY_MAPPING = _DEFAULT_MAPPINGS_DIR / "seasonal_survey_default.yaml"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments for the pipeline runner."""
    parser = argparse.ArgumentParser(
        description="Run the GIS/AutoCAD data-merge pipeline headlessly."
    )
    parser.add_argument("base_file", type=Path, help="Path to the base (system) Excel file.")
    parser.add_argument("secondary_file", type=Path, help="Path to the secondary Excel file.")
    parser.add_argument(
        "output_path",
        type=Path,
        nargs="?",
        default=None,
        help="Output .xlsx path (default: timestamped filename in the current directory).",
    )
    parser.add_argument("--base-mapping", type=Path, default=_DEFAULT_BASE_MAPPING)
    parser.add_argument("--secondary-mapping", type=Path, default=_DEFAULT_SECONDARY_MAPPING)
    parser.add_argument(
        "--no-sort", action="store_true", help="Disable spatial sorting of the output."
    )
    return parser.parse_args(argv)


def run_pipeline(args: argparse.Namespace) -> Path:
    """Run the read -> merge -> sort -> write pipeline and return the output path."""
    base_config = load_mapping(args.base_mapping)
    secondary_config = load_mapping(args.secondary_mapping)

    base_reader = BaseFileReader(args.base_file, base_config)
    secondary_mapper = YamlColumnMapper(secondary_config["fields"])
    secondary_reader = SecondaryFileReader(args.secondary_file, secondary_mapper, secondary_config)
    sorter = None if args.no_sort else SpatialSorter(DEFAULT_LANDMARK_KEYWORDS)

    logger.info("Reading and merging sources...")
    result = MergeParcelsUseCase(base_reader, secondary_reader, spatial_sorter=sorter).execute()
    logger.info(f"Merged {len(result.parcels)} parcels ({len(result.warnings)} warnings).")
    for warning in result.warnings:
        logger.warning(warning)

    output_path = args.output_path or Path.cwd() / default_output_filename()
    ExportFinalFileUseCase(ProfessionalExcelWriter()).execute(result.parcels, output_path)
    logger.info(f"Wrote output to {output_path}")
    return output_path


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns a process exit code."""
    configure_logging()
    args = parse_args(argv)

    start = time.time()
    try:
        run_pipeline(args)
    except Exception as exc:  # CLI boundary: convert any failure to a clean exit code
        logger.error(f"Pipeline failed: {exc}")
        return 1
    elapsed = time.time() - start

    logger.info(f"Done in {elapsed:.2f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
