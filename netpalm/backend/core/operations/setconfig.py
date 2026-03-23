"""SetConfig operation — executes configuration changes via southbound drivers.

Also handles dryrun when instantiated with ``dry_run=True``.
"""

from __future__ import annotations

import logging
from typing import Any

from netpalm.backend.core.confload.confload import NetpalmSettings
from netpalm.backend.core.driver.driver_auto_loader import DriverRegistry
from netpalm.backend.core.operations import BaseOperation
from netpalm.backend.core.operations.checks import run_checks
from netpalm.backend.core.utilities.jinja2.j2 import render_j2template
from netpalm.backend.core.utilities.webhook.webhook import exec_webhook_func

log = logging.getLogger(__name__)


class SetConfigOperation(BaseOperation):
    def __init__(self, dry_run: bool = False) -> None:
        self._dry_run = dry_run

    def execute(
        self,
        kwargs: dict[str, Any],
        driver_registry: DriverRegistry,
        settings: NetpalmSettings,
    ) -> dict[str, Any]:
        library = kwargs.get("library", "")
        config: str | list[str] = kwargs.get("config", "")
        j2conf = kwargs.get("j2config")
        webhook = kwargs.get("webhook")
        pre_checks = kwargs.get("pre_checks")
        post_checks = kwargs.get("post_checks")
        enable_mode = kwargs.get("enable_mode", False)

        # Render Jinja2 template if provided
        if j2conf:
            j2confargs = j2conf.get("args")
            res = render_j2template(j2conf["template"], template_type="config", kwargs=j2confargs)
            config = res["data"]["task_result"]["template_render_result"]
            if library == "ncclient":
                if not kwargs.get("args"):
                    kwargs["args"] = {}
                kwargs["args"]["config"] = config

        driver_cls = driver_registry.get(library)
        driver_obj = driver_cls(**kwargs)
        sesh = driver_obj.connect()

        if pre_checks:
            run_checks(driver_obj, sesh, pre_checks, "PreCheck")

        if self._dry_run:
            result = (
                driver_obj.config(sesh, config, dry_run=True, enable_mode=enable_mode)
                if enable_mode
                else driver_obj.config(sesh, config, dry_run=True)
            )
        else:
            result = (
                driver_obj.config(sesh, config, enable_mode=enable_mode)
                if enable_mode
                else driver_obj.config(sesh, config)
            )

        if post_checks:
            run_checks(driver_obj, sesh, post_checks, "PostCheck")

        driver_obj.logout(sesh)

        if webhook:
            exec_webhook_func(jobdata={"task_result": result}, webhook_payload=webhook)

        return result
