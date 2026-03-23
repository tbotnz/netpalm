"""Operations layer — typed task handlers dispatched by the executor."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from netpalm.backend.core.confload.confload import NetpalmSettings
from netpalm.backend.core.driver.driver_auto_loader import DriverRegistry

log = logging.getLogger(__name__)


class BaseOperation(ABC):
    """Base class for all executor operations."""

    @abstractmethod
    def execute(
        self,
        kwargs: dict[str, Any],
        driver_registry: DriverRegistry,
        settings: NetpalmSettings,
    ) -> dict[str, Any]:
        """Execute the operation and return results."""


class OperationRegistry:
    """Maps method names to operation handler instances."""

    def __init__(self) -> None:
        self._ops: dict[str, BaseOperation] = {}

    def register(self, method: str, operation: BaseOperation) -> None:
        self._ops[method] = operation

    def get(self, method: str) -> BaseOperation:
        op = self._ops.get(method)
        if op is None:
            raise ValueError(f"No operation registered for method '{method}'")
        return op

    @property
    def available(self) -> list[str]:
        return list(self._ops.keys())

    def load_defaults(self) -> None:
        """Register all built-in operations."""
        from netpalm.backend.core.operations.getconfig import GetConfigOperation
        from netpalm.backend.core.operations.script import ScriptOperation
        from netpalm.backend.core.operations.service import ServiceOperation
        from netpalm.backend.core.operations.setconfig import SetConfigOperation

        self.register("getconfig", GetConfigOperation())
        self.register("setconfig", SetConfigOperation())
        self.register("dryrun", SetConfigOperation(dry_run=True))
        self.register("script", ScriptOperation())
        for action in ("create", "update", "delete", "re_deploy", "validate", "health_check"):
            self.register(f"service_{action}", ServiceOperation(action))
