"""
NetpalmDriver — abstract base class for all southbound drivers.

Every driver must:
  - Set a class-level `driver_name` string
  - Implement connect(), sendcommand(), config(), logout()
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

log = logging.getLogger(__name__)


class NetpalmDriver(ABC):
    """Abstract base class defining the southbound driver contract."""

    driver_name: str  # subclasses must set this as a class attribute

    @abstractmethod
    def connect(self) -> Any:
        """Establish a connection to the device. Return the session object."""

    @abstractmethod
    def sendcommand(self, session: Any, command: list[str]) -> dict[str, Any]:
        """Send read commands to the device. Return a result dict."""

    @abstractmethod
    def config(self, session: Any, command: str | list[str], **kwargs: Any) -> dict[str, Any]:
        """Send configuration commands to the device. Return a result dict."""

    @abstractmethod
    def logout(self, session: Any) -> None:
        """Close the session / disconnect from the device."""
