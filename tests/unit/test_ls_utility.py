"""Tests for the ls (list files) utility."""

from __future__ import annotations

import os
import tempfile
from unittest.mock import patch

import pytest


class TestLsUtility:
    @pytest.fixture()
    def tmpdir(self):
        with tempfile.TemporaryDirectory() as d:
            yield d

    @patch("netpalm.backend.core.utilities.ls.ls.config")
    def test_list_config_templates(self, mock_config, tmpdir):
        mock_config.jinja2_config_templates = tmpdir + "/"
        # Create some j2 files
        for name in ["template_a.j2", "template_b.j2"]:
            with open(os.path.join(tmpdir, name), "w") as f:
                f.write("test")

        from netpalm.backend.core.utilities.ls.ls import ls

        lister = ls(folder="config")
        result = lister.getfiles()
        assert result["status"] == "success"
        templates = result["data"]["task_result"]["templates"]
        assert "template_a" in templates
        assert "template_b" in templates

    @patch("netpalm.backend.core.utilities.ls.ls.config")
    def test_list_scripts(self, mock_config, tmpdir):
        mock_config.custom_scripts = tmpdir + "/"
        for name in ["script_one.py", "script_two.py", "__init__.py"]:
            with open(os.path.join(tmpdir, name), "w") as f:
                f.write("pass")

        from netpalm.backend.core.utilities.ls.ls import ls

        lister = ls(folder="script")
        result = lister.getfiles()
        assert result["status"] == "success"
        templates = result["data"]["task_result"]["templates"]
        # __init__.py should be filtered out
        assert all("__init__" not in t for t in templates)
        assert "script_one" in templates

    @patch("netpalm.backend.core.utilities.ls.ls.config")
    def test_list_empty_dir(self, mock_config, tmpdir):
        mock_config.jinja2_config_templates = tmpdir + "/"

        from netpalm.backend.core.utilities.ls.ls import ls

        lister = ls(folder="config")
        result = lister.getfiles()
        assert result["status"] == "success"
        assert result["data"]["task_result"]["templates"] == []

    @patch("netpalm.backend.core.utilities.ls.ls.config")
    def test_list_filters_pycache(self, mock_config, tmpdir):
        mock_config.custom_scripts = tmpdir + "/"
        pycache_dir = os.path.join(tmpdir, "__pycache__")
        os.makedirs(pycache_dir)
        with open(os.path.join(pycache_dir, "cached.py"), "w") as f:
            f.write("pass")
        with open(os.path.join(tmpdir, "real_script.py"), "w") as f:
            f.write("pass")

        from netpalm.backend.core.utilities.ls.ls import ls

        lister = ls(folder="script")
        result = lister.getfiles()
        templates = result["data"]["task_result"]["templates"]
        assert all("__pycache__" not in t for t in templates)

    @patch("netpalm.backend.core.utilities.ls.ls.config")
    def test_list_files_function(self, mock_config, tmpdir):
        mock_config.jinja2_config_templates = tmpdir + "/"
        with open(os.path.join(tmpdir, "my.j2"), "w") as f:
            f.write("test")

        from netpalm.backend.core.utilities.ls.ls import list_files

        result = list_files(fldr="config")
        assert result["status"] == "success"

    @patch("netpalm.backend.core.utilities.ls.ls.config")
    def test_list_filters_model_py(self, mock_config, tmpdir):
        mock_config.python_service_templates = tmpdir + "/"
        with open(os.path.join(tmpdir, "service_model.py"), "w") as f:
            f.write("pass")
        with open(os.path.join(tmpdir, "real_service.py"), "w") as f:
            f.write("pass")

        from netpalm.backend.core.utilities.ls.ls import ls

        lister = ls(folder="service")
        result = lister.getfiles()
        templates = result["data"]["task_result"]["templates"]
        assert all("_model" not in t for t in templates)
