"""Tests for DriverRegistry — auto-loading driver plugins."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from netpalm.backend.core.driver.driver_auto_loader import (
    DriverNotFoundError,
    DriverRegistry,
)
from netpalm.backend.core.driver.netpalm_driver import NetpalmDriver


class FakeDriver(NetpalmDriver):
    driver_name = "fake"

    def connect(self):
        return MagicMock()

    def sendcommand(self, session, command):
        return {"output": "fake"}

    def config(self, session, command, **kwargs):
        return {"output": "configured"}

    def logout(self, session):
        pass


class TestDriverRegistry:
    @pytest.fixture()
    def registry(self, mock_settings):
        return DriverRegistry(settings=mock_settings)

    def test_initial_empty(self, registry):
        assert registry.available == []

    def test_get_not_found(self, registry):
        with pytest.raises(DriverNotFoundError) as exc_info:
            registry.get("nonexistent")
        assert exc_info.value.library == "nonexistent"
        assert "nonexistent" in str(exc_info.value)

    def test_manual_register_and_get(self, registry):
        registry._map["fake"] = FakeDriver
        assert registry.get("fake") is FakeDriver
        assert "fake" in registry.available

    def test_available_lists_all(self, registry):
        registry._map["a"] = FakeDriver
        registry._map["b"] = FakeDriver
        assert sorted(registry.available) == ["a", "b"]

    def test_load_nonexistent_directory(self, mock_settings):
        mock_settings.drivers = "/nonexistent/dir"
        registry = DriverRegistry(settings=mock_settings)
        registry.load()  # should not raise
        assert registry.available == []

    def test_load_discovers_drivers(self, mock_settings):
        """Integration-style: load real driver directory."""
        import os

        if not os.path.isdir(mock_settings.drivers):
            pytest.skip("driver directory not found")

        registry = DriverRegistry(settings=mock_settings)
        registry.load()
        # At minimum, netmiko/napalm/ncclient should be discovered
        assert len(registry.available) >= 1


class TestDriverNotFoundError:
    def test_attributes(self):
        err = DriverNotFoundError("puresnmp")
        assert err.library == "puresnmp"
        assert "puresnmp" in str(err)
