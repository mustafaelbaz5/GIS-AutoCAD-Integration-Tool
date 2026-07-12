"""Application entry point.

Per Iteration 4, launches the pywebview shell instead of the old
PySide6 window. See `presentation/app_window.py` and
`presentation/search_window.py`.
"""

from pathlib import Path

import webview

from src.infrastructure.logging_setup import configure_logging
from src.presentation.api.main_api import MainApi
from src.presentation.api.search_api import SearchApi
from src.presentation.app_window import create_main_window
from src.presentation.search_window import create_search_window


def main() -> None:
    """Launch the application windows."""
    configure_logging()

    search_window: webview.Window | None = None
    search_api: SearchApi | None = None

    def open_search_window(last_output_path: Path | None) -> None:
        nonlocal search_window, search_api
        if search_window is not None and search_api is not None:
            if last_output_path is not None:
                search_api.load_output_file(str(last_output_path))
                search_window.evaluate_js("refreshAfterExternalReload()")
            search_window.show()
            return
        search_window, search_api = create_search_window(last_output_path)

    main_api = MainApi(open_search_window=open_search_window)
    create_main_window(main_api)

    webview.start()


if __name__ == "__main__":
    main()
