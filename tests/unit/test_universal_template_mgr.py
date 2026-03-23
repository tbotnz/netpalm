"""Tests for the universal template manager utility."""

from __future__ import annotations

import base64
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest


class TestUniversalTemplateMgr:
    @pytest.fixture()
    def tmpdir(self):
        with tempfile.TemporaryDirectory() as d:
            yield d

    @pytest.fixture()
    def mock_config(self, tmpdir):
        cfg = MagicMock()
        cfg.jinja2_config_templates = tmpdir + "/j2_config/"
        cfg.python_service_templates = tmpdir + "/services/"
        cfg.webhook_jinja2_templates = tmpdir + "/j2_webhook/"
        cfg.ttp_templates = tmpdir + "/ttp/"
        cfg.custom_scripts = tmpdir + "/scripts/"
        cfg.custom_webhooks = tmpdir + "/webhooks/"
        # Create dirs
        for attr in [
            cfg.jinja2_config_templates,
            cfg.python_service_templates,
            cfg.webhook_jinja2_templates,
            cfg.ttp_templates,
            cfg.custom_scripts,
            cfg.custom_webhooks,
        ]:
            os.makedirs(attr, exist_ok=True)
        return cfg

    @patch("netpalm.backend.core.utilities.universal_template_mgr.unvrsl.config")
    @patch("netpalm.backend.core.utilities.universal_template_mgr.unvrsl.reload_extensibles_func")
    def test_add_template(self, mock_reload, mock_config_ref, mock_config, tmpdir):
        mock_config_ref.jinja2_config_templates = mock_config.jinja2_config_templates
        mock_config_ref.python_service_templates = mock_config.python_service_templates
        mock_config_ref.webhook_jinja2_templates = mock_config.webhook_jinja2_templates
        mock_config_ref.ttp_templates = mock_config.ttp_templates
        mock_config_ref.custom_scripts = mock_config.custom_scripts
        mock_config_ref.custom_webhooks = mock_config.custom_webhooks

        from netpalm.backend.core.utilities.universal_template_mgr.unvrsl import unvrsl

        mgr = unvrsl()
        content = "hostname {{ hostname }}"
        b64 = base64.b64encode(content.encode()).decode()
        result = mgr.add_template(
            payload={
                "route_type": "j2_config_templates",
                "name": "test_tmpl",
                "base64_payload": b64,
            }
        )
        assert result["status"] == "success"
        assert result["data"]["task_result"]["added"] == "test_tmpl"

        # Verify file was written
        path = os.path.join(mock_config.jinja2_config_templates, "test_tmpl.j2")
        assert os.path.exists(path)
        with open(path) as f:
            assert f.read() == content

    @patch("netpalm.backend.core.utilities.universal_template_mgr.unvrsl.config")
    @patch("netpalm.backend.core.utilities.universal_template_mgr.unvrsl.reload_extensibles_func")
    def test_get_template(self, mock_reload, mock_config_ref, mock_config, tmpdir):
        mock_config_ref.custom_scripts = mock_config.custom_scripts

        # Write a file first
        path = os.path.join(mock_config.custom_scripts, "my_script.py")
        with open(path, "w") as f:
            f.write("print('hello')")

        from netpalm.backend.core.utilities.universal_template_mgr.unvrsl import unvrsl

        mgr = unvrsl()
        result = mgr.get_template(payload={"route_type": "custom_scripts", "name": "my_script"})
        assert result["status"] == "success"
        decoded = base64.b64decode(result["data"]["task_result"]["base64_payload"]).decode()
        assert decoded == "print('hello')"

    @patch("netpalm.backend.core.utilities.universal_template_mgr.unvrsl.config")
    @patch("netpalm.backend.core.utilities.universal_template_mgr.unvrsl.reload_extensibles_func")
    def test_remove_template(self, mock_reload, mock_config_ref, mock_config, tmpdir):
        mock_config_ref.custom_scripts = mock_config.custom_scripts

        path = os.path.join(mock_config.custom_scripts, "to_delete.py")
        with open(path, "w") as f:
            f.write("pass")

        from netpalm.backend.core.utilities.universal_template_mgr.unvrsl import unvrsl

        mgr = unvrsl()
        result = mgr.remove_template(payload={"route_type": "custom_scripts", "name": "to_delete"})
        assert result["status"] == "success"
        assert not os.path.exists(path)

    @patch("netpalm.backend.core.utilities.universal_template_mgr.unvrsl.config")
    @patch("netpalm.backend.core.utilities.universal_template_mgr.unvrsl.reload_extensibles_func")
    def test_remove_nonexistent(self, mock_reload, mock_config_ref, mock_config, tmpdir):
        mock_config_ref.custom_scripts = mock_config.custom_scripts

        from netpalm.backend.core.utilities.universal_template_mgr.unvrsl import unvrsl

        mgr = unvrsl()
        result = mgr.remove_template(payload={"route_type": "custom_scripts", "name": "nonexistent"})
        assert result["status"] == "error"

    @patch("netpalm.backend.core.utilities.universal_template_mgr.unvrsl.config")
    def test_get_nonexistent_template(self, mock_config_ref, mock_config, tmpdir):
        mock_config_ref.custom_scripts = mock_config.custom_scripts

        from netpalm.backend.core.utilities.universal_template_mgr.unvrsl import unvrsl

        mgr = unvrsl()
        result = mgr.get_template(payload={"route_type": "custom_scripts", "name": "nope"})
        assert result["status"] == "error"
