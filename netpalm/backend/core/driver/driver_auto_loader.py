"""
DriverRegistry — scans the drivers directory at startup and auto-loads
all NetpalmDriver subclasses.

Usage:
    registry = DriverRegistry(settings)
    registry.load()
    driver_cls = registry.get("netmiko")
"""

from __future__ import annotations

import importlib
import logging
import os

from netpalm.backend.core.confload.confload import NetpalmSettings, get_settings
from netpalm.backend.core.driver.netpalm_driver import NetpalmDriver

log = logging.getLogger(__name__)


class DriverNotFoundError(Exception):
    """Raised when a requested driver name is not registered."""

    def __init__(self, library: str) -> None:
        super().__init__(f"Driver '{library}' not found in registry")
        self.library = library


class DriverRegistry:
    """
    Scans `settings.drivers` directory and registers all NetpalmDriver subclasses.
    """

    def __init__(self, settings: NetpalmSettings | None = None) -> None:
        self._settings = settings or get_settings()
        self._map: dict[str, type[NetpalmDriver]] = {}

    def load(self) -> None:
        """Scan driver directory and import all NetpalmDriver subclasses."""
        driver_dir = self._settings.drivers
        driver_dir_module_path = driver_dir.replace("/", ".").rstrip(".")

        if not os.path.isdir(driver_dir):
            log.warning(f"DriverRegistry: driver directory not found: {driver_dir}")
            return

        for driver_pkg in os.listdir(driver_dir):
            pkg_path = os.path.join(driver_dir, driver_pkg)
            if not os.path.isdir(pkg_path):
                continue
            for filename in os.listdir(pkg_path):
                if not filename.endswith(".py") or filename.startswith("__"):
                    continue
                module_name = filename[:-3]
                full_module = f"{driver_dir_module_path}.{driver_pkg}.{module_name}"
                try:
                    module = importlib.import_module(full_module)
                except Exception as exc:
                    log.error(f"DriverRegistry: failed to import {full_module}: {exc}")
                    continue
                for obj in module.__dict__.values():
                    if (
                        isinstance(obj, type)
                        and issubclass(obj, NetpalmDriver)
                        and obj is not NetpalmDriver
                        and hasattr(obj, "driver_name")
                        and obj.driver_name
                    ):
                        self._map[obj.driver_name] = obj
                        log.debug(f"DriverRegistry: loaded driver '{obj.driver_name}'")

        log.info(f"DriverRegistry: loaded {len(self._map)} driver(s): {list(self._map)}")

    def get(self, library: str) -> type[NetpalmDriver]:
        """Return the driver class for `library`; raise DriverNotFoundError if missing."""
        cls = self._map.get(library)
        if cls is None:
            raise DriverNotFoundError(library)
        return cls

    @property
    def available(self) -> list[str]:
        return list(self._map.keys())
