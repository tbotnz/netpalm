"""Tests for the Jinja2 template utility."""

from __future__ import annotations

import os
import tempfile
from unittest.mock import patch

import pytest


class TestJ2Utility:
    @pytest.fixture()
    def tmpdir(self):
        with tempfile.TemporaryDirectory() as d:
            yield d

    @patch("netpalm.backend.core.utilities.jinja2.j2.config")
    def test_render_j2template_config(self, mock_config, tmpdir):
        mock_config.jinja2_config_templates = tmpdir + "/"

        # Write a template file
        with open(os.path.join(tmpdir, "test.j2"), "w") as f:
            f.write("hostname {{ hostname }}")

        from netpalm.backend.core.utilities.jinja2.j2 import j2

        renderer = j2(j2_type="config")
        result = renderer.render_j2template("test", kwargs={"hostname": "switch1"})
        assert result["status"] == "success"
        assert result["data"]["task_result"]["template_render_result"] == "hostname switch1"

    @patch("netpalm.backend.core.utilities.jinja2.j2.config")
    def test_render_j2template_webhook(self, mock_config, tmpdir):
        mock_config.webhook_jinja2_templates = tmpdir + "/"

        with open(os.path.join(tmpdir, "webhook.j2"), "w") as f:
            f.write('{"device": "{{ device }}"}')

        from netpalm.backend.core.utilities.jinja2.j2 import j2

        renderer = j2(j2_type="webhook")
        result = renderer.render_j2template("webhook", kwargs={"device": "router1"})
        assert result["status"] == "success"
        assert '"router1"' in result["data"]["task_result"]["template_render_result"]

    @patch("netpalm.backend.core.utilities.jinja2.j2.config")
    def test_gettemplate_success(self, mock_config, tmpdir):
        mock_config.jinja2_config_templates = tmpdir + "/"

        template_content = "interface {{ interface }}\n ip address {{ ip }}"
        with open(os.path.join(tmpdir, "iface.j2"), "w") as f:
            f.write(template_content)

        from netpalm.backend.core.utilities.jinja2.j2 import j2

        renderer = j2(j2_type="config")
        result = renderer.gettemplate("iface")
        assert result["status"] == "success"
        assert result["data"]["task_result"]["template_data"] == template_content

    @patch("netpalm.backend.core.utilities.jinja2.j2.config")
    def test_gettemplate_not_found(self, mock_config, tmpdir):
        mock_config.jinja2_config_templates = tmpdir + "/"

        from netpalm.backend.core.utilities.jinja2.j2 import j2

        renderer = j2(j2_type="config")
        result = renderer.gettemplate("nonexistent")
        # opentemplate returns an exception, which gettemplate wraps
        assert result is not None

    @patch("netpalm.backend.core.utilities.jinja2.j2.config")
    def test_render_j2template_function(self, mock_config, tmpdir):
        mock_config.jinja2_config_templates = tmpdir + "/"

        with open(os.path.join(tmpdir, "func_test.j2"), "w") as f:
            f.write("vlan {{ vlan_id }}")

        from netpalm.backend.core.utilities.jinja2.j2 import render_j2template

        result = render_j2template("func_test", template_type="config", kwargs={"vlan_id": "100"})
        assert result["status"] == "success"
        assert "vlan 100" in result["data"]["task_result"]["template_render_result"]

    @patch("netpalm.backend.core.utilities.jinja2.j2.config")
    def test_j2gettemplate_function(self, mock_config, tmpdir):
        mock_config.jinja2_config_templates = tmpdir + "/"

        with open(os.path.join(tmpdir, "get_test.j2"), "w") as f:
            f.write("template data here")

        from netpalm.backend.core.utilities.jinja2.j2 import j2gettemplate

        result = j2gettemplate("get_test", template_type="config")
        assert result["status"] == "success"
