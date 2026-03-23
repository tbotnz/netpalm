"""Script operation — dynamically loads and executes user-defined Python scripts."""
from __future__ import annotations

import importlib
import inspect
import logging
from typing import Any

from netpalm.backend.core.confload.confload import NetpalmSettings
from netpalm.backend.core.driver.driver_auto_loader import DriverRegistry
from netpalm.backend.core.models.models import Script, ScriptCustom
from netpalm.backend.core.operations import BaseOperation
from netpalm.backend.core.utilities.webhook.webhook import exec_webhook_func

log = logging.getLogger(__name__)


def _find_script_model(script_name: str, settings: NetpalmSettings) -> tuple[type, bool]:
    """Discover a ScriptCustom subclass inside the script module.

    Returns:
        (model_class, model_defined) — model_defined is True when a custom
        ScriptCustom subclass was found in the script file.
    """
    module_path = settings.custom_scripts.replace("/", ".") + script_name

    try:
        module = importlib.import_module(module_path)
        run_fn = getattr(module, "run")
        for item in inspect.getfullargspec(run_fn):
            if isinstance(item, dict):
                for _key, value in item.items():
                    if isinstance(value, type) and issubclass(value, ScriptCustom):
                        return value, True
    except Exception:
        log.debug(f"_find_script_model: no custom model found for {script_name}")

    return Script, False


class ScriptOperation(BaseOperation):
    def execute(
        self,
        kwargs: dict[str, Any],
        driver_registry: DriverRegistry,
        settings: NetpalmSettings,
    ) -> dict[str, Any]:
        script_name = kwargs["script"]
        webhook = kwargs.get("webhook")
        args = kwargs.get("args")

        model_cls, model_defined = _find_script_model(script_name, settings)

        module_path = settings.custom_scripts.replace("/", ".") + script_name
        log.debug(f"ScriptOperation: importing {module_path}")
        module = importlib.import_module(module_path)
        run_fn = getattr(module, "run")

        if model_defined:
            data = model_cls(**kwargs)
            result = run_fn(data)
        else:
            result = run_fn(kwargs=args)

        if webhook:
            exec_webhook_func(jobdata={"task_result": result}, webhook_payload=webhook)

        return result
