"""Tests for the operations layer."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from netpalm.backend.core.operations import BaseOperation, OperationRegistry
from netpalm.backend.core.operations.checks import run_checks
from netpalm.exceptions import NetpalmCheckError


class TestOperationRegistry:
    def test_load_defaults_registers_all_methods(self):
        registry = OperationRegistry()
        registry.load_defaults()
        expected = {
            "getconfig",
            "setconfig",
            "dryrun",
            "script",
            "service_create",
            "service_update",
            "service_delete",
            "service_re_deploy",
            "service_validate",
            "service_health_check",
        }
        assert set(registry.available) == expected

    def test_get_unknown_method_raises(self):
        registry = OperationRegistry()
        with pytest.raises(ValueError, match="No operation registered"):
            registry.get("nonexistent")

    def test_register_and_get(self):
        registry = OperationRegistry()
        mock_op = Mock(spec=BaseOperation)
        registry.register("test_op", mock_op)
        assert registry.get("test_op") is mock_op


class TestRunChecks:
    def test_include_passes(self):
        driver = Mock()
        driver.sendcommand.return_value = {"output": "hostname router1"}
        checks = [
            {
                "get_config_args": {"command": "show hostname"},
                "match_str": ["router1"],
                "match_type": "include",
            }
        ]
        run_checks(driver, Mock(), checks, "PostCheck")

    def test_include_fails(self):
        driver = Mock()
        driver.sendcommand.return_value = {"output": "hostname router1"}
        checks = [
            {
                "get_config_args": {"command": "show hostname"},
                "match_str": ["router99"],
                "match_type": "include",
            }
        ]
        with pytest.raises(NetpalmCheckError, match="PostCheck Failed"):
            run_checks(driver, Mock(), checks, "PostCheck")

    def test_exclude_passes(self):
        driver = Mock()
        driver.sendcommand.return_value = {"output": "hostname router1"}
        checks = [
            {
                "get_config_args": {"command": "show hostname"},
                "match_str": ["router99"],
                "match_type": "exclude",
            }
        ]
        run_checks(driver, Mock(), checks, "PreCheck")

    def test_exclude_fails(self):
        driver = Mock()
        driver.sendcommand.return_value = {"output": "hostname router1"}
        checks = [
            {
                "get_config_args": {"command": "show hostname"},
                "match_str": ["router1"],
                "match_type": "exclude",
            }
        ]
        with pytest.raises(NetpalmCheckError, match="PreCheck Failed"):
            run_checks(driver, Mock(), checks, "PreCheck")

    def test_multiple_checks(self):
        driver = Mock()
        driver.sendcommand.return_value = {"output": "hostname router1 version 15"}
        checks = [
            {
                "get_config_args": {"command": "show version"},
                "match_str": ["router1"],
                "match_type": "include",
            },
            {
                "get_config_args": {"command": "show version"},
                "match_str": ["badstring"],
                "match_type": "exclude",
            },
        ]
        run_checks(driver, Mock(), checks, "PostCheck")
