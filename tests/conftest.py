"""Shared fixtures for the netpalm test suite."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture()
def mock_settings():
    """Return a mock NetpalmSettings with sensible defaults."""
    settings = MagicMock()
    settings.kafka_fifo_topic = "netpalm.jobs.fifo"
    settings.kafka_pinned_topic_prefix = "netpalm.jobs.pinned"
    settings.kafka_results_topic = "netpalm.results"
    settings.kafka_consumer_group = "netpalm-workers"
    settings.kafka_bootstrap_servers = "localhost:9092"
    settings.scheduler_poll_interval_seconds = 5
    settings.database_url = "sqlite+aiosqlite://"
    settings.drivers = "netpalm/backend/plugins/drivers/"
    settings.event_listeners_dir = "netpalm/backend/plugins/event_listeners/"
    settings.custom_scripts = "netpalm/backend/plugins/extensibles/custom_scripts/"
    settings.jinja2_config_templates = "netpalm/backend/plugins/extensibles/j2_config_templates/"
    settings.python_service_templates = "netpalm/backend/plugins/extensibles/services/"
    settings.ttp_templates = "netpalm/backend/plugins/extensibles/ttp_templates/"
    settings.custom_webhooks = "netpalm/backend/plugins/extensibles/custom_webhooks/"
    settings.webhook_jinja2_templates = "netpalm/backend/plugins/extensibles/j2_webhook_templates/"
    settings.default_webhook_name = "default_webhook"
    settings.txtfsm_index_file = "netpalm/backend/plugins/extensibles/ntc-templates/index"
    settings.redis_cache_enabled = True
    settings.redis_cache_default_timeout = 300
    settings.redis_cache_key_prefix = "NETPALM_RESULT_CACHE"
    return settings


@pytest.fixture()
def sample_task_id():
    return uuid.uuid4()


@pytest.fixture()
def sample_job_record(sample_task_id):
    """Return a mock JobRecord."""
    job = MagicMock()
    job.task_id = sample_task_id
    job.method = "getconfig"
    job.queue_strategy = "fifo"
    job.pinned_host = None
    job.status = "pending"
    job.payload = {"host": "10.0.0.1", "command": "show version"}
    job.result = None
    job.error = None
    job.created_at = datetime.now(timezone.utc)
    job.started_at = None
    job.ended_at = None
    return job
