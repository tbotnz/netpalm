"""
EventListener — abstract base class for user-defined event listeners.

Users subclass this, implement parse() and on_event(), drop the file into
the event_listeners_dir plugin directory, and the EventListenerRegistry
auto-discovers and registers it at startup.

Example:
    class MySyslogListener(EventListener):
        topics = ["netpalm.events.syslog"]

        def parse(self, raw: bytes) -> NetpalmEvent | None:
            try:
                payload = json.loads(raw)
                return NetpalmEvent(
                    source_topic="netpalm.events.syslog",
                    device_host=payload.get("host"),
                    event_type="syslog",
                    raw=raw,
                    data=payload,
                )
            except Exception:
                return None

        async def on_event(self, event: NetpalmEvent, manager: NetpalmManager) -> None:
            await manager.get_config(...)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from netpalm.backend.core.models.models import NetpalmEvent

if TYPE_CHECKING:
    from netpalm.backend.core.manager.netpalm_manager import NetpalmManager


class EventListener(ABC):
    """
    ABC for user-defined event listeners.

    Subclasses must:
      - Set `topics: list[str]` as a class attribute
      - Implement `parse(raw) -> NetpalmEvent | None`
      - Implement `async on_event(event, manager) -> None`
    """

    topics: list[str]  # Kafka topics this listener subscribes to

    @abstractmethod
    def parse(self, raw: bytes) -> NetpalmEvent | None:
        """
        Parse raw Kafka message bytes into a NetpalmEvent.
        Return None to discard the message (no action taken).
        """

    @abstractmethod
    async def on_event(self, event: NetpalmEvent, manager: NetpalmManager) -> None:
        """
        React to a parsed event. Use manager to schedule tasks:
            await manager.get_config(...)
            await manager.set_config(...)
            await manager.create_service(...)
        """
