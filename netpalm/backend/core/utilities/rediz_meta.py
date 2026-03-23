"""Driver error helpers.

These are kept for backward compatibility with southbound driver plugins
that catch-and-reraise via write_meta_error.  New code should simply let
exceptions propagate — the executor catches them.
"""
from __future__ import annotations

import logging

log = logging.getLogger(__name__)


def write_meta_error(exception: Exception) -> None:
    """Re-raise the exception so the executor can handle it."""
    log.exception("write_meta_error: driver error")
    raise exception


def write_meta_error_string(data: str) -> None:
    """Raise a plain exception with the given message."""
    raise Exception(f"failed: {data}")
