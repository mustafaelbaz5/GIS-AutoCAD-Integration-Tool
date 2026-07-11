"""Integration test for MainViewModel: exercises the real GUI-to-use-case wiring.

Real drag-and-drop can't be simulated headlessly, so this drives the
view-model directly (as the drop zones' `file_selected` signal would)
against the real sample files, verifying that progress/log signals are
actually emitted end-to-end and a valid output file is produced.
"""

from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication
from src.presentation.viewmodels.main_viewmodel import MainViewModel

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BASE_FILE_PATH = PROJECT_ROOT / "الاخوه.xlsx"
SECONDARY_FILE_PATH = PROJECT_ROOT / "حصر الصيفي2026 جديد  اول.xlsx"


def test_run_pipeline_emits_progress_and_produces_output(
    tmp_path: Path, qapp: QApplication
) -> None:
    if not BASE_FILE_PATH.exists() or not SECONDARY_FILE_PATH.exists():
        pytest.skip("Real sample files not present")

    viewmodel = MainViewModel()
    viewmodel.set_base_file(str(BASE_FILE_PATH))
    viewmodel.set_secondary_file(str(SECONDARY_FILE_PATH))
    viewmodel.set_output_dir(str(tmp_path))

    progress_events: list[tuple[int, str]] = []
    log_events: list[tuple[str, str]] = []
    finished_events: list[tuple[bool, str]] = []

    viewmodel.progress_changed.connect(lambda p, m: progress_events.append((p, m)))
    viewmodel.log_emitted.connect(lambda m, level: log_events.append((m, level)))
    viewmodel.finished.connect(lambda ok, path: finished_events.append((ok, path)))

    viewmodel.run_pipeline()

    assert progress_events[0][0] == 0
    assert progress_events[-1][0] == 100
    assert any(level == "success" for _, level in log_events)
    assert finished_events == [(True, finished_events[0][1])]
    assert Path(finished_events[0][1]).exists()
