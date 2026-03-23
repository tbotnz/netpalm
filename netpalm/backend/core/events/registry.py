"""
EventListenerRegistry — discovers EventListener subclasses from the
event_listeners_dir plugin directory at startup.

Maintains a topic → [listener, ...] mapping and dispatches incoming
Kafka messages to all matching listeners.
"""
from __future__ import annotations

import importlib
import logging
import os
from collections import defaultdict
from typing import TYPE_CHECKING, Any

from netpalm.backend.core.confload.confload import NetpalmSettings, get_settings
from netpalm.backend.plugins.event_listeners.base import EventListener

if TYPE_CHECKING:
    from netpalm.backend.core.manager.netpalm_manager import NetpalmManager

log = logging.getLogger(__name__)


class EventListenerLoadError(Exception):
    """Raised when an EventListener subclass is missing required attributes."""


class EventListenerRegistry:
    """
    Discovers EventListener subclasses from event_listeners_dir at startup.
    Maintains a topic → [listener, ...] mapping.
    """

    def __init__(
        self,
        manager: "NetpalmManager",
        settings: NetpalmSettings | None = None,
    ) -> None:
        self._manager = manager
        self._settings = settings or get_settings()
        self._registry: dict[str, list[EventListener]] = defaultdict(list)

    def load(self) -> None:
        """
        Scan event_listeners_dir, import all EventListener subclasses,
        register each against its declared topics.
        """
        listeners_dir = self._settings.event_listeners_dir
        if not os.path.isdir(listeners_dir):
            log.warning(f"EventListenerRegistry: directory not found: {listeners_dir}")
            return

        module_prefix = listeners_dir.replace("/", ".").rstrip(".")

        for filename in os.listdir(listeners_dir):
            if not filename.endswith(".py") or filename.startswith("__"):
                continue
            module_name = filename[:-3]
            full_module = f"{module_prefix}.{module_name}"
            try:
                module = importlib.import_module(full_module)
            except Exception as exc:
                log.error(f"EventListenerRegistry: failed to import {full_module}: {exc}")
                continue

            for obj in module.__dict__.values():
                if (
                    isinstance(obj, type)
                    and issubclass(obj, EventListener)
                    and obj is not EventListener
                ):
                    self._validate_and_register(obj)

        log.info(
            f"EventListenerRegistry: loaded listeners for topics: {list(self._registry)}"
        )

    def _validate_and_register(self, cls: type[EventListener]) -> None:
        """Validate required attributes and register the listener."""
        if not hasattr(cls, "topics") or not cls.topics:
            raise EventListenerLoadError(
                f"{cls.__name__} is missing required 'topics' class attribute"
            )
        if not hasattr(cls, "parse"):
            raise EventListenerLoadError(f"{cls.__name__} is missing 'parse' method")
        if not hasattr(cls, "on_event"):
            raise EventListenerLoadError(f"{cls.__name__} is missing 'on_event' method")

        instance = cls()
        for topic in cls.topics:
            self._registry[topic].append(instance)
            log.debug(f"EventListenerRegistry: registered {cls.__name__} → {topic}")

    def get_topics(self) -> list[str]:
        """Return all topics that have at least one registered listener."""
        return list(self._registry.keys())

    async def dispatch(self, topic: str, raw: bytes) -> None:
        """
        For each listener registered on topic:
          event = listener.parse(raw)
          if event: await listener.on_event(event, manager)
        """
        listeners = self._registry.get(topic, [])
        for listener in listeners:
            try:
                event = listener.parse(raw)
                if event is not None:
                    await listener.on_event(event, self._manager)
            except Exception as exc:
                log.error(
                    f"EventListenerRegistry.dispatch: error in {type(listener).__name__} "
                    f"on topic {topic}: {exc}"
                )
