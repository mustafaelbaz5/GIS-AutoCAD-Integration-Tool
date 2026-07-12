"""pywebview window bootstrap for the second, independent Search window.

Per Iteration 4 Task C §8.2.E, this opens as a real separate OS-level
window (`webview.create_window`), not a modal over the main window.
"""

from pathlib import Path

import webview

from src.presentation.api.search_api import SearchApi
from src.shared.paths import get_app_root

_WINDOW_TITLE = "بحث في الحيازات"


def create_search_window(
    initial_output_path: Path | None = None,
) -> tuple[webview.Window, SearchApi]:
    """Create the search pywebview window, bound to a fresh `SearchApi`.

    Per Task E §10.2, the window must work whether it obtains its data
    from the main window's last-generated output (`initial_output_path`,
    preloaded here before the window even opens) or via its own "افتح
    ملف مختلف" flow (`SearchApi.open_different_file`) once open. Both
    paths funnel through `SearchApi.load_output_file`.

    Returns both the window and its `SearchApi`, so the caller can
    reload a newer output into an already-open window later (see
    `main.py`'s `open_search_window` closure).
    """
    api = SearchApi()
    if initial_output_path is not None:
        api.load_output_file(str(initial_output_path))

    html_path = get_app_root() / "src" / "presentation" / "web" / "search.html"
    window = webview.create_window(
        _WINDOW_TITLE,
        url=str(html_path),
        js_api=api,
        width=900,
        height=700,
        min_size=(600, 400),
    )
    if window is None:
        raise RuntimeError("webview.create_window() failed to create the search window")
    api.bind_window(window)
    return window, api
