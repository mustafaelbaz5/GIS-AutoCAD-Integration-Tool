"""Runs the pipeline off the GUI thread, per project brief Phase 8.

`MainViewModel` is not itself moved to the worker thread — only this
thin `QObject` is. When `run()` executes on the worker thread, calling
`viewmodel.run_pipeline()` emits the view-model's signals from that
thread; Qt's auto connection safely queues delivery to slots living on
the GUI thread (e.g. widgets connected in `MainWindow`).
"""

from PySide6.QtCore import QObject

from src.presentation.viewmodels.main_viewmodel import MainViewModel


class PipelineWorker(QObject):
    """Thin QObject whose `run()` slot executes on a background QThread."""

    def __init__(self, viewmodel: MainViewModel) -> None:
        super().__init__()
        self._viewmodel = viewmodel

    def run(self) -> None:
        """Run the view-model's pipeline. Invoked via `QThread.started`."""
        self._viewmodel.run_pipeline()
