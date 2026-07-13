"""pywebview window bootstrap for the main window, per Iteration 4."""

import json
from typing import Any

import webview
from loguru import logger
from webview.dom import DOMEventHandler

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
        text_select=True,  # pywebview disables text selection by default
    )
    if window is None:
        raise RuntimeError("webview.create_window() failed to create the main window")
    api.bind_window(window)
    window.events.loaded += lambda: _setup_drag_drop(window)
    return window


def _setup_drag_drop(window: webview.Window) -> None:
    """Bind document-level drag-and-drop handlers that resolve real file paths.

    Standard HTML5 DnD doesn't expose real filesystem paths in
    WebView2/Chromium; pywebview's `window.dom` API taps into
    WebView2's native file-drop mechanism instead, which does. Bound
    at `document` level (not on the drop-zone elements themselves)
    since those elements get destroyed and recreated on every
    `main.js` re-render — a binding on a specific element would go
    stale the moment the user picks a file or the screen changes.
    `prevent_default=True` on all three events stops WebView2 from
    navigating the whole window to the dropped file, which is its
    default behavior otherwise.
    """

    def on_drop(e: dict[str, Any]) -> None:
        files = e.get("dataTransfer", {}).get("files", [])
        logger.info(f"Native drop event received, {len(files)} file(s)")
        if not files:
            return
        full_path = files[0].get("pywebviewFullPath")
        if not full_path:
            logger.warning("Dropped file has no pywebviewFullPath; ignoring")
            return
        window.evaluate_js(f"window.onNativeFileDropped({json.dumps(full_path)})")

    # pywebview's type stubs declare Event.__iadd__ as Callable[..., Any]
    # only, but the runtime explicitly special-cases DOMEventHandler
    # (see webview/dom/element.py's Element.on) — a stub gap, not a
    # real type error.
    window.dom.document.events.dragenter += DOMEventHandler(  # type: ignore[arg-type]
        lambda e: None, prevent_default=True
    )
    window.dom.document.events.dragover += DOMEventHandler(  # type: ignore[arg-type]
        lambda e: None, prevent_default=True, debounce=200
    )
    window.dom.document.events.drop += DOMEventHandler(  # type: ignore[arg-type]
        on_drop, prevent_default=True
    )
