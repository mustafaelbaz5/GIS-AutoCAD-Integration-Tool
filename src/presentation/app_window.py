"""pywebview window bootstrap for the main window.

Replaces `views/main_window.py` (PySide6) per Iteration 4. The old
PySide6 presentation modules are left in place, untouched, until Task
D/E fully replace their functionality — deleting them now would strand
in-progress work without a working replacement yet.
"""

import webview

from src.presentation.api.main_api import MainApi
from src.shared.paths import get_app_root

_WINDOW_TITLE = "أداة معالجة بيانات الحيازات الزراعية"


def create_main_window(api: MainApi) -> webview.Window:
    """Create the main pywebview window, bound to `api`.

    Args:
        api: The `MainApi` instance to expose to this window's JS as
            `window.pywebview.api`. Its `bind_window` is called here
            once the `webview.Window` exists.
    """
    html_path = get_app_root() / "src" / "presentation" / "web" / "main.html"
    window = webview.create_window(
        _WINDOW_TITLE,
        url=str(html_path),
        js_api=api,
        width=1440,
        height=960,
        min_size=(1024, 720),
    )
    if window is None:
        raise RuntimeError("webview.create_window() failed to create the main window")
    api.bind_window(window)
    return window
