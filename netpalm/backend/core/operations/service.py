"""Service operation — dynamic service class loading and lifecycle dispatch.

Also contains the NetpalmService ABC that user-defined services subclass.
"""

from __future__ import annotations

import importlib
import inspect
import logging
from typing import Any

from pydantic import BaseModel

from netpalm.backend.core.confload.confload import NetpalmSettings
from netpalm.backend.core.driver.driver_auto_loader import DriverRegistry
from netpalm.backend.core.operations import BaseOperation

log = logging.getLogger(__name__)


class NetpalmService:
    """Base class for user-defined service implementations."""

    def __init__(self, model: type[BaseModel], service_id: str | None = None) -> None:
        self.model = model
        self.service_id = service_id

    def create(self, model_data: BaseModel) -> Any:
        log.info("netpalm service: create method not implemented on your service")

    def update(self, model_data: BaseModel) -> Any:
        log.info("netpalm service: update method not implemented on your service")

    def delete(self, model_data: BaseModel) -> Any:
        log.info("netpalm service: delete method not implemented on your service")

    def re_deploy(self, model_data: BaseModel) -> Any:
        log.info("netpalm service: re_deploy method not implemented on your service")

    def validate(self, model_data: BaseModel) -> Any:
        log.info("netpalm service: validate method not implemented on your service")

    def health_check(self, model_data: BaseModel) -> Any:
        log.info("netpalm service: health_check method not implemented on your service")


def _get_service(service_name: str, settings: NetpalmSettings) -> dict[str, Any]:
    """Import a service module and return its model and service class."""
    module_path = settings.python_service_templates.replace("/", ".") + service_name
    log.debug(f"_get_service: importing {module_path}")
    module = importlib.import_module(module_path)

    result: dict[str, Any] = {"service_model": None, "service_class": None}
    for _name, obj in inspect.getmembers(module, inspect.isclass):
        if issubclass(obj, BaseModel) and obj is not BaseModel:
            result["service_model"] = obj
        if issubclass(obj, NetpalmService) and obj is not NetpalmService:
            result["service_class"] = obj
    return result


class ServiceOperation(BaseOperation):
    """Dispatches a service lifecycle action (create, update, delete, etc.)."""

    def __init__(self, action: str) -> None:
        self._action = action

    def execute(
        self,
        kwargs: dict[str, Any],
        driver_registry: DriverRegistry,
        settings: NetpalmSettings,
    ) -> dict[str, Any]:
        service_name = kwargs["service_model"]
        service_id = kwargs.get("service_id")
        user_data = kwargs.get("data", {})

        service_lookup = _get_service(service_name, settings)
        svc = service_lookup["service_class"](service_lookup["service_model"], service_id)

        method = getattr(svc, self._action)
        return method(service_lookup["service_model"](**user_data))  # type: ignore[no-any-return]
