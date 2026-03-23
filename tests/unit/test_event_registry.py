"""Tests for EventListenerRegistry — plugin discovery and dispatch."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from netpalm.backend.core.events.registry import (
    EventListenerLoadError,
    EventListenerRegistry,
)
from netpalm.backend.core.models.models import NetpalmEvent
from netpalm.backend.plugins.event_listeners.base import EventListener

# ── Test listeners ──────────────────────────────────────────────────────────


class ValidListener(EventListener):
    topics = ["netpalm.events.syslog"]

    def parse(self, raw: bytes) -> NetpalmEvent | None:
        data = json.loads(raw)
        return NetpalmEvent(
            source_topic="netpalm.events.syslog",
            event_type="syslog",
            raw=raw,
            data=data,
        )

    async def on_event(self, event, manager):
        pass


class ListenerMissingTopics(EventListener):
    # Missing 'topics'
    def parse(self, raw):
        return None

    async def on_event(self, event, manager):
        pass


class ListenerEmptyTopics(EventListener):
    topics = []

    def parse(self, raw):
        return None

    async def on_event(self, event, manager):
        pass


# ── Tests ──────────────────────────────────────────────────────────────────


class TestEventListenerRegistry:
    @pytest.fixture()
    def registry(self, mock_settings):
        manager = MagicMock()
        return EventListenerRegistry(manager=manager, settings=mock_settings)

    def test_initial_state_empty(self, registry):
        assert registry.get_topics() == []

    def test_validate_and_register_valid(self, registry):
        registry._validate_and_register(ValidListener)
        assert "netpalm.events.syslog" in registry.get_topics()

    def test_validate_and_register_missing_topics(self, registry):
        with pytest.raises(EventListenerLoadError, match="missing required 'topics'"):
            registry._validate_and_register(ListenerMissingTopics)

    def test_validate_and_register_empty_topics(self, registry):
        with pytest.raises(EventListenerLoadError, match="missing required 'topics'"):
            registry._validate_and_register(ListenerEmptyTopics)

    def test_multiple_listeners_same_topic(self, registry):
        class AnotherSyslog(EventListener):
            topics = ["netpalm.events.syslog"]

            def parse(self, raw):
                return None

            async def on_event(self, event, manager):
                pass

        registry._validate_and_register(ValidListener)
        registry._validate_and_register(AnotherSyslog)
        assert registry.get_topics() == ["netpalm.events.syslog"]
        assert len(registry._registry["netpalm.events.syslog"]) == 2

    def test_listener_with_multiple_topics(self, registry):
        class MultiTopicListener(EventListener):
            topics = ["topic.a", "topic.b"]

            def parse(self, raw):
                return None

            async def on_event(self, event, manager):
                pass

        registry._validate_and_register(MultiTopicListener)
        assert "topic.a" in registry.get_topics()
        assert "topic.b" in registry.get_topics()

    async def test_dispatch_calls_listener(self, registry):
        registry._validate_and_register(ValidListener)

        listener_instance = registry._registry["netpalm.events.syslog"][0]
        listener_instance.on_event = AsyncMock()

        raw = json.dumps({"msg": "test syslog"}).encode()
        await registry.dispatch("netpalm.events.syslog", raw)

        listener_instance.on_event.assert_awaited_once()

    async def test_dispatch_unknown_topic(self, registry):
        # Should not raise, just no-op
        await registry.dispatch("unknown.topic", b"data")

    async def test_dispatch_parse_returns_none_skips_on_event(self, registry):
        class DiscardingListener(EventListener):
            topics = ["topic.discard"]

            def parse(self, raw):
                return None  # discard everything

            async def on_event(self, event, manager):
                pass

        registry._validate_and_register(DiscardingListener)
        listener_instance = registry._registry["topic.discard"][0]
        listener_instance.on_event = AsyncMock()

        await registry.dispatch("topic.discard", b"anything")
        listener_instance.on_event.assert_not_awaited()

    async def test_dispatch_exception_in_listener_logged_not_raised(self, registry):
        class FailingListener(EventListener):
            topics = ["topic.fail"]

            def parse(self, raw):
                return NetpalmEvent(
                    source_topic="topic.fail",
                    event_type="test",
                    raw=raw,
                    data={},
                )

            async def on_event(self, event, manager):
                raise RuntimeError("boom")

        registry._validate_and_register(FailingListener)
        # Should not raise — errors are logged
        await registry.dispatch("topic.fail", b"data")

    def test_load_nonexistent_directory(self, mock_settings):
        mock_settings.event_listeners_dir = "/nonexistent/dir"
        manager = MagicMock()
        registry = EventListenerRegistry(manager=manager, settings=mock_settings)
        registry.load()  # should not raise
        assert registry.get_topics() == []
