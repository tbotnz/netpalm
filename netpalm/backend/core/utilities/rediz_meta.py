"""
rediz_meta.py — driver error helpers.

Previously used RQ's get_current_job() to write errors into job metadata.
Now simply raises the exception so the NetpalmExecutor can catch it and
write the error to the PostgreSQL jobs table.
"""
from __future__ import annotations

import inspect
import logging

log = logging.getLogger(__name__)


def exception_full_name(exception: BaseException) -> str:
    name = exception.__class__.__name__
    if (module := inspect.getmodule(exception)) is None:
        return name
    return f"{module.__name__}.{name}"


def write_meta_error(exception: Exception) -> None:
    """Re-raise the exception so the executor can handle it."""
    log.exception("write_meta_error: driver error")
    raise exception


def write_meta_error_string(data: str) -> None:
    """Raise a plain exception with the given message."""
    raise Exception(f"failed: {data}")


def write_mandatory_meta() -> None:
    """No-op — job metadata is now written by the executor."""
    pass


def render_netpalm_payload(job_result: dict | None = None) -> dict:
    """No-op shim — result rendering is handled by the executor."""
    return {"task_result": job_result or {}}
