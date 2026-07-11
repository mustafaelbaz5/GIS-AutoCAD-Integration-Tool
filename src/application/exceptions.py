"""Application-layer exceptions."""


class PipelineCancelledError(Exception):
    """Raised when a running pipeline is cancelled by the user."""
