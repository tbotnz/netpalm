"""Route dispatch map — maps method names to callable operations.

Used by template/script routers for direct (non-queued) calls.
Queued operations go through the executor's OperationRegistry instead.
"""

from __future__ import annotations

from typing import Any

from netpalm.backend.core.confload.confload import get_settings
from netpalm.backend.core.driver.driver_auto_loader import DriverRegistry
from netpalm.backend.core.operations.getconfig import GetConfigOperation
from netpalm.backend.core.operations.script import ScriptOperation
from netpalm.backend.core.operations.service import ServiceOperation
from netpalm.backend.core.operations.setconfig import SetConfigOperation
from netpalm.backend.core.utilities.jinja2.j2 import j2gettemplate, render_j2template
from netpalm.backend.core.utilities.ls.ls import list_files
from netpalm.backend.core.utilities.textfsm.template import (
    addtemplate,
    gettemplate,
    listtemplates,
    pushtemplate,
    removetemplate,
)

# Lazy-initialised singletons for direct (non-queued) operation calls.
_registry: DriverRegistry | None = None
_settings = None


def _ensure_initialized() -> tuple[DriverRegistry, Any]:
    global _registry, _settings
    if _registry is None:
        _settings = get_settings()
        _registry = DriverRegistry(_settings)
        _registry.load()
    return _registry, _settings


def _exec_command(**kwargs: Any) -> Any:
    reg, settings = _ensure_initialized()
    return GetConfigOperation().execute(kwargs, reg, settings)


def _exec_config(**kwargs: Any) -> Any:
    reg, settings = _ensure_initialized()
    return SetConfigOperation().execute(kwargs, reg, settings)


def _dryrun(**kwargs: Any) -> Any:
    reg, settings = _ensure_initialized()
    return SetConfigOperation(dry_run=True).execute(kwargs, reg, settings)


def _script_kiddy(**kwargs: Any) -> Any:
    reg, settings = _ensure_initialized()
    return ScriptOperation().execute(kwargs, reg, settings)


def _service_op(action: str) -> Any:
    def _run(**kwargs: Any) -> Any:
        reg, settings = _ensure_initialized()
        return ServiceOperation(action).execute(kwargs, reg, settings)

    return _run


routes = {
    "getconfig": _exec_command,
    "setconfig": _exec_config,
    "listtemplates": listtemplates,
    "gettemplate": gettemplate,
    "addtemplate": addtemplate,
    "pushtemplate": pushtemplate,
    "removetemplate": removetemplate,
    "ls": list_files,
    "script": _script_kiddy,
    "j2gettemplate": j2gettemplate,
    "render_j2template": render_j2template,
    "dryrun": _dryrun,
    "service_create": _service_op("create"),
    "service_update": _service_op("update"),
    "service_delete": _service_op("delete"),
    "service_re_deploy": _service_op("re_deploy"),
    "service_validate": _service_op("validate"),
    "service_health_check": _service_op("health_check"),
}
