"""Tests for the webhook runner utility."""
from __future__ import annotations

from unittest.mock import MagicMock, patch


class TestWebhookRunner:
    @patch("netpalm.backend.core.utilities.webhook.webhook.config")
    def test_init_sets_name(self, mock_config):
        mock_config.custom_webhooks = "netpalm/backend/plugins/extensibles/custom_webhooks/"
        mock_config.default_webhook_name = "default_webhook"

        from netpalm.backend.core.utilities.webhook.webhook import webhook_runner

        runner = webhook_runner({"name": "my_hook", "args": {"key": "val"}})
        assert runner.webhook_raw_name == "my_hook"
        assert runner.webhook_args == {"key": "val"}
        assert "my_hook" in runner.webhook_name

    @patch("netpalm.backend.core.utilities.webhook.webhook.config")
    def test_init_no_j2template(self, mock_config):
        mock_config.custom_webhooks = "netpalm/backend/plugins/extensibles/custom_webhooks/"
        mock_config.default_webhook_name = "default_webhook"

        from netpalm.backend.core.utilities.webhook.webhook import webhook_runner

        runner = webhook_runner({"name": "hook"})
        assert runner.webhook_j2_name is None

    @patch("netpalm.backend.core.utilities.webhook.webhook.config")
    def test_init_with_j2template(self, mock_config):
        mock_config.custom_webhooks = "netpalm/backend/plugins/extensibles/custom_webhooks/"
        mock_config.default_webhook_name = "default_webhook"

        from netpalm.backend.core.utilities.webhook.webhook import webhook_runner

        runner = webhook_runner({"name": "hook", "j2template": "my_j2"})
        assert runner.webhook_j2_name == "my_j2"

    @patch("netpalm.backend.core.utilities.webhook.webhook.importlib")
    @patch("netpalm.backend.core.utilities.webhook.webhook.config")
    def test_webhook_exec_success(self, mock_config, mock_importlib):
        mock_config.custom_webhooks = "webhooks/"
        mock_config.default_webhook_name = "default_webhook"

        mock_module = MagicMock()
        mock_module.run_webhook.return_value = {"status": "ok"}
        mock_importlib.import_module.return_value = mock_module

        from netpalm.backend.core.utilities.webhook.webhook import webhook_runner

        runner = webhook_runner({"name": "test_hook"})
        result = runner.webhook_exec({"data": "test"})
        assert result == {"status": "ok"}
        mock_module.run_webhook.assert_called_once()

    @patch("netpalm.backend.core.utilities.webhook.webhook.importlib")
    @patch("netpalm.backend.core.utilities.webhook.webhook.config")
    def test_webhook_exec_failure(self, mock_config, mock_importlib):
        mock_config.custom_webhooks = "webhooks/"
        mock_config.default_webhook_name = "default_webhook"

        mock_importlib.import_module.side_effect = ImportError("no module")

        from netpalm.backend.core.utilities.webhook.webhook import webhook_runner

        runner = webhook_runner({"name": "bad_hook"})
        result = runner.webhook_exec({"data": "test"})
        assert isinstance(result, Exception)

    @patch("netpalm.backend.core.utilities.webhook.webhook.importlib")
    @patch("netpalm.backend.core.utilities.webhook.webhook.config")
    def test_exec_webhook_func(self, mock_config, mock_importlib):
        mock_config.custom_webhooks = "webhooks/"
        mock_config.default_webhook_name = "default_webhook"

        mock_module = MagicMock()
        mock_module.run_webhook.return_value = {"sent": True}
        mock_importlib.import_module.return_value = mock_module

        from netpalm.backend.core.utilities.webhook.webhook import exec_webhook_func

        result = exec_webhook_func(
            jobdata={"result": "data"},
            webhook_payload={"name": "hook"},
        )
        assert result == {"sent": True}
