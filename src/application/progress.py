"""Progress-reporting callback type shared by use cases.

A plain callable rather than a Qt signal so the application layer
stays framework-agnostic — the presentation layer adapts this to
whatever UI signal mechanism it uses.
"""

from collections.abc import Callable

ProgressCallback = Callable[[int, str], None]
