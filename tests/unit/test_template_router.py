"""Tests for the template router — TextFSM, J2, scripts, webhooks, services."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from netpalm.routers.template import router

app = FastAPI()
app.include_router(router)


@pytest.fixture()
def client():
    return TestClient(app, raise_server_exceptions=False)


class TestTextFSMRoutes:
    @patch("netpalm.routers.template.routes")
    def test_list_templates(self, mock_routes, client):
        mock_routes.__getitem__ = MagicMock(
            return_value=MagicMock(
                return_value={"status": "success", "data": {"task_result": {"templates": ["a", "b"]}}}
            )
        )
        resp = client.get("/template")
        assert resp.status_code == 200

    @patch("netpalm.routers.template.routes")
    def test_get_template(self, mock_routes, client):
        mock_routes.__getitem__ = MagicMock(
            return_value=MagicMock(return_value={"status": "success", "data": {"task_result": "template content"}})
        )
        resp = client.get("/template/test_template")
        assert resp.status_code == 200

    @patch("netpalm.routers.template.add_transaction_log_entry")
    @patch("netpalm.routers.template.routes")
    def test_delete_template(self, mock_routes, mock_log, client):
        mock_routes.__getitem__ = MagicMock(return_value=MagicMock(return_value=None))
        resp = client.request("DELETE", "/template", json={"template": "old_template"})
        assert resp.status_code == 204


class TestJ2ConfigRoutes:
    @patch("netpalm.routers.template.routes")
    def test_list_config_j2_templates(self, mock_routes, client):
        mock_routes.__getitem__ = MagicMock(
            return_value=MagicMock(return_value={"status": "success", "data": {"task_result": {"templates": []}}})
        )
        resp = client.get("/j2template/config/")
        assert resp.status_code == 200

    @patch("netpalm.routers.template.add_transaction_log_entry")
    @patch("netpalm.routers.template.unvrsl")
    def test_add_config_j2_template(self, mock_unvrsl, mock_log, client):
        mock_instance = MagicMock()
        mock_instance.add_template.return_value = {"status": "success", "data": {"task_result": {"added": "test"}}}
        mock_unvrsl.return_value = mock_instance

        resp = client.post(
            "/j2template/config/",
            json={"base64_payload": "dGVzdA==", "name": "test_template"},
        )
        assert resp.status_code == 200

    @patch("netpalm.routers.template.add_transaction_log_entry")
    @patch("netpalm.routers.template.unvrsl")
    def test_remove_config_j2_template(self, mock_unvrsl, mock_log, client):
        mock_instance = MagicMock()
        mock_instance.remove_template.return_value = None
        mock_unvrsl.return_value = mock_instance

        resp = client.request(
            "DELETE", "/j2template/config/", json={"name": "test_template"}
        )
        assert resp.status_code == 204


class TestJ2WebhookRoutes:
    @patch("netpalm.routers.template.routes")
    def test_list_webhook_j2_templates(self, mock_routes, client):
        mock_routes.__getitem__ = MagicMock(
            return_value=MagicMock(return_value={"status": "success", "data": {"task_result": {"templates": []}}})
        )
        resp = client.get("/j2template/webhook/")
        assert resp.status_code == 200


class TestJ2RenderRoutes:
    @patch("netpalm.routers.template.routes")
    def test_render_config_template(self, mock_routes, client):
        mock_routes.__getitem__ = MagicMock(
            return_value=MagicMock(
                return_value={"status": "success", "data": {"task_result": {"template_render_result": "rendered"}}}
            )
        )
        resp = client.post(
            "/j2template/render/config/my_template", json={"hostname": "switch1"}
        )
        assert resp.status_code == 201

    @patch("netpalm.routers.template.routes")
    def test_render_webhook_template(self, mock_routes, client):
        mock_routes.__getitem__ = MagicMock(
            return_value=MagicMock(
                return_value={"status": "success", "data": {"task_result": {"template_render_result": "rendered"}}}
            )
        )
        resp = client.post(
            "/j2template/render/webhook/my_template", json={"data": "value"}
        )
        assert resp.status_code == 201


class TestScriptRoutes:
    @patch("netpalm.routers.template.add_transaction_log_entry")
    @patch("netpalm.routers.template.unvrsl")
    def test_add_script(self, mock_unvrsl, mock_log, client):
        mock_instance = MagicMock()
        mock_instance.add_template.return_value = {"status": "success", "data": {"task_result": {"added": "myscript"}}}
        mock_unvrsl.return_value = mock_instance

        resp = client.post(
            "/script/add/",
            json={"base64_payload": "cHJpbnQoJ2hpJyk=", "name": "myscript"},
        )
        assert resp.status_code == 200

    @patch("netpalm.routers.template.unvrsl")
    def test_get_script(self, mock_unvrsl, client):
        mock_instance = MagicMock()
        mock_instance.get_template.return_value = {"status": "success", "data": {"task_result": {"base64_payload": "dGVzdA=="}}}
        mock_unvrsl.return_value = mock_instance

        resp = client.get("/script/myscript")
        assert resp.status_code == 200

    @patch("netpalm.routers.template.add_transaction_log_entry")
    @patch("netpalm.routers.template.unvrsl")
    def test_remove_script(self, mock_unvrsl, mock_log, client):
        mock_instance = MagicMock()
        mock_instance.remove_template.return_value = None
        mock_unvrsl.return_value = mock_instance

        resp = client.request(
            "DELETE", "/script/remove/", json={"name": "myscript"}
        )
        assert resp.status_code == 204


class TestWebhookScriptRoutes:
    @patch("netpalm.routers.template.add_transaction_log_entry")
    @patch("netpalm.routers.template.unvrsl")
    def test_add_webhook_script(self, mock_unvrsl, mock_log, client):
        mock_instance = MagicMock()
        mock_instance.add_template.return_value = {"status": "success", "data": {"task_result": {"added": "hook"}}}
        mock_unvrsl.return_value = mock_instance

        resp = client.post(
            "/webhook/add/",
            json={"base64_payload": "dGVzdA==", "name": "hook"},
        )
        assert resp.status_code == 200


class TestServiceTemplateRoutes:
    @patch("netpalm.routers.template.add_transaction_log_entry")
    @patch("netpalm.routers.template.unvrsl")
    def test_add_service_file(self, mock_unvrsl, mock_log, client):
        mock_instance = MagicMock()
        mock_instance.add_template.return_value = {"status": "success", "data": {"task_result": {"added": "svc"}}}
        mock_unvrsl.return_value = mock_instance

        resp = client.post(
            "/service/add/",
            json={"base64_payload": "dGVzdA==", "name": "svc"},
        )
        assert resp.status_code == 200

    @patch("netpalm.routers.template.unvrsl")
    def test_get_service_file(self, mock_unvrsl, client):
        mock_instance = MagicMock()
        mock_instance.get_template.return_value = {"status": "success", "data": {"task_result": {"base64_payload": "dGVzdA=="}}}
        mock_unvrsl.return_value = mock_instance

        resp = client.get("/service/svc")
        assert resp.status_code == 200

    @patch("netpalm.routers.template.add_transaction_log_entry")
    @patch("netpalm.routers.template.unvrsl")
    def test_remove_service_file(self, mock_unvrsl, mock_log, client):
        mock_instance = MagicMock()
        mock_instance.remove_template.return_value = None
        mock_unvrsl.return_value = mock_instance

        resp = client.request(
            "DELETE", "/service/remove/", json={"name": "svc"}
        )
        assert resp.status_code == 204


class TestTTPRoutes:
    @patch("netpalm.routers.template.routes")
    def test_list_ttp_templates(self, mock_routes, client):
        mock_routes.__getitem__ = MagicMock(
            return_value=MagicMock(return_value={"status": "success", "data": {"task_result": {"templates": []}}})
        )
        resp = client.get("/ttptemplate/")
        assert resp.status_code == 200

    @patch("netpalm.routers.template.unvrsl")
    def test_get_ttp_template(self, mock_unvrsl, client):
        mock_instance = MagicMock()
        mock_instance.get_template.return_value = {"status": "success", "data": {"task_result": {"base64_payload": "dGVzdA=="}}}
        mock_unvrsl.return_value = mock_instance

        resp = client.get("/ttptemplate/my_ttp")
        assert resp.status_code == 200

    @patch("netpalm.routers.template.add_transaction_log_entry")
    @patch("netpalm.routers.template.unvrsl")
    def test_add_ttp_template(self, mock_unvrsl, mock_log, client):
        mock_instance = MagicMock()
        mock_instance.add_template.return_value = {"status": "success", "data": {"task_result": {"added": "ttp"}}}
        mock_unvrsl.return_value = mock_instance

        resp = client.post(
            "/ttptemplate/",
            json={"base64_payload": "dGVzdA==", "name": "my_ttp"},
        )
        assert resp.status_code == 200

    @patch("netpalm.routers.template.add_transaction_log_entry")
    @patch("netpalm.routers.template.unvrsl")
    def test_remove_ttp_template(self, mock_unvrsl, mock_log, client):
        mock_instance = MagicMock()
        mock_instance.remove_template.return_value = None
        mock_unvrsl.return_value = mock_instance

        resp = client.request(
            "DELETE", "/ttptemplate/", json={"name": "my_ttp"}
        )
        assert resp.status_code == 204
