"""Tests for the OperationRegistry."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from netpalm.backend.core.operations import BaseOperation, OperationRegistry


class FakeOperation(BaseOperation):
    def execute(self, kwargs, driver_registry, settings):
        return {"result": "ok"}


class TestOperationRegistry:
    def test_register_and_get(self):
        reg = OperationRegistry()
        op = FakeOperation()
        reg.register("test_op", op)
        assert reg.get("test_op") is op

    def test_get_missing_raises(self):
        reg = OperationRegistry()
        with pytest.raises(ValueError, match="No operation registered"):
            reg.get("nonexistent")

    def test_available(self):
        reg = OperationRegistry()
        reg.register("a", FakeOperation())
        reg.register("b", FakeOperation())
        assert sorted(reg.available) == ["a", "b"]

    def test_load_defaults(self):
        reg = OperationRegistry()
        reg.load_defaults()
        assert "getconfig" in reg.available
        assert "setconfig" in reg.available
        assert "dryrun" in reg.available
        assert "script" in reg.available
        assert "service_create" in reg.available
        assert "service_update" in reg.available
        assert "service_delete" in reg.available
        assert "service_re_deploy" in reg.available
        assert "service_validate" in reg.available
        assert "service_health_check" in reg.available

    def test_execute(self):
        reg = OperationRegistry()
        reg.register("fake", FakeOperation())
        result = reg.get("fake").execute({}, MagicMock(), MagicMock())
        assert result == {"result": "ok"}
