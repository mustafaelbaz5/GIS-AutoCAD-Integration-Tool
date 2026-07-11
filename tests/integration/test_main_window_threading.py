"""Integration test: MainWindow's background-thread pipeline execution.

Real drag-and-drop and a real mouse click on the success dialog can't
be simulated headlessly, so this drives the window's internal slots
directly against the real sample files, running the actual QThread
machinery (not a synchronous call) to verify the UI stays responsive,
progress/log signals arrive, cancellation works, and the thread is
always torn down cleanly (no orphans).
"""

import time
from collections.abc import Callable
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication
from src.presentation.views.main_window import MainWindow

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BASE_FILE_PATH = PROJECT_ROOT / "الاخوه.xlsx"
SECONDARY_FILE_PATH = PROJECT_ROOT / "حصر الصيفي2026 جديد  اول.xlsx"


def _process_events_until(
    condition: Callable[[], bool], app: QApplication, timeout_s: float = 60.0
) -> None:
    start = time.time()
    while not condition():
        app.processEvents()
        if time.time() - start > timeout_s:
            raise TimeoutError("Condition not met within timeout")


def _make_window_with_real_files(tmp_path: Path) -> MainWindow:
    window = MainWindow()
    window._viewmodel.set_base_file(str(BASE_FILE_PATH))
    window._viewmodel.set_secondary_file(str(SECONDARY_FILE_PATH))
    window._viewmodel.set_output_dir(str(tmp_path))
    return window


def test_start_runs_on_background_thread_and_cleans_up(
    tmp_path: Path, qapp: QApplication, monkeypatch: pytest.MonkeyPatch
) -> None:
    if not BASE_FILE_PATH.exists() or not SECONDARY_FILE_PATH.exists():
        pytest.skip("Real sample files not present")

    window = _make_window_with_real_files(tmp_path)
    monkeypatch.setattr(window, "_show_success_dialog", lambda output_path: None)

    events: list[tuple[bool, str]] = []
    window._viewmodel.finished.connect(lambda ok, path: events.append((ok, path)))

    window._on_start_clicked()

    assert window._start_button.isEnabled() is False
    assert window._cancel_button.isEnabled() is True
    assert window._thread is not None
    assert window._thread.isRunning()

    _process_events_until(lambda: bool(events), qapp)
    _process_events_until(lambda: window._thread is None, qapp)

    assert events == [(True, events[0][1])]
    assert Path(events[0][1]).exists()
    assert window._start_button.isEnabled() is True
    assert window._cancel_button.isEnabled() is False
    assert window._thread is None
    assert window._worker is None


def test_cancel_stops_the_pipeline_and_tears_down_the_thread_cleanly(
    tmp_path: Path, qapp: QApplication, monkeypatch: pytest.MonkeyPatch
) -> None:
    if not BASE_FILE_PATH.exists() or not SECONDARY_FILE_PATH.exists():
        pytest.skip("Real sample files not present")

    window = _make_window_with_real_files(tmp_path)
    monkeypatch.setattr(window, "_show_success_dialog", lambda output_path: None)

    events: list[tuple[bool, str]] = []
    log_levels: list[str] = []
    window._viewmodel.finished.connect(lambda ok, path: events.append((ok, path)))
    window._viewmodel.log_emitted.connect(lambda message, level: log_levels.append(level))

    window._on_start_clicked()
    window._on_cancel_clicked()

    _process_events_until(lambda: bool(events), qapp)
    _process_events_until(lambda: window._thread is None, qapp)

    assert events == [(False, "")]
    assert "warning" in log_levels
    assert window._thread is None
    assert window._worker is None
