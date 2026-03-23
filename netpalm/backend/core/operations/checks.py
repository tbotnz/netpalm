"""Shared pre/post check validation for getconfig and setconfig operations."""

from __future__ import annotations

import logging
from typing import Any

from netpalm.backend.core.driver.netpalm_driver import NetpalmDriver
from netpalm.exceptions import NetpalmCheckError

log = logging.getLogger(__name__)


def run_checks(
    driver: NetpalmDriver,
    session: Any,
    checks: list[dict[str, Any]],
    label: str,
) -> None:
    """Run pre/post check commands and raise NetpalmCheckError on mismatch.

    Args:
        driver: Connected driver instance.
        session: Active driver session.
        checks: List of check dicts with ``get_config_args``, ``match_str``, ``match_type``.
        label: Human-readable label for error messages (e.g. "PreCheck", "PostCheck").
    """
    for check in checks:
        cmd = check["get_config_args"]["command"]
        result = driver.sendcommand(session, [cmd])
        for matchstr in check["match_str"]:
            if check["match_type"] == "include" and matchstr not in str(result):
                raise NetpalmCheckError(f"{label} Failed: {matchstr} not found in {result}")
            if check["match_type"] == "exclude" and matchstr in str(result):
                raise NetpalmCheckError(f"{label} Failed: {matchstr} found in {result}")
