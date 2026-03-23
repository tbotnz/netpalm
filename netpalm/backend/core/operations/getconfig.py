"""GetConfig operation — executes read-only commands via southbound drivers."""
from __future__ import annotations

import logging
from typing import Any

from netpalm.backend.core.confload.confload import NetpalmSettings
from netpalm.backend.core.driver.driver_auto_loader import DriverRegistry
from netpalm.backend.core.operations import BaseOperation
from netpalm.backend.core.operations.checks import run_checks
from netpalm.backend.core.utilities.webhook.webhook import exec_webhook_func

log = logging.getLogger(__name__)


class GetConfigOperation(BaseOperation):
    def execute(
        self,
        kwargs: dict[str, Any],
        driver_registry: DriverRegistry,
        settings: NetpalmSettings,
    ) -> dict[str, Any]:
        library = kwargs.get("library", "")
        command = kwargs.get("command")
        webhook = kwargs.get("webhook")
        post_checks = kwargs.get("post_checks")

        driver_cls = driver_registry.get(library)
        driver_obj = driver_cls(**kwargs)
        sesh = driver_obj.connect()

        commandlst = [command] if isinstance(command, str) else command
        result = driver_obj.sendcommand(sesh, commandlst) if commandlst else driver_obj.sendcommand(sesh)

        if post_checks:
            run_checks(driver_obj, sesh, post_checks, "PostCheck")

        driver_obj.logout(sesh)

        if webhook:
            exec_webhook_func(jobdata={"task_result": result}, webhook_payload=webhook)

        return result
