"""Tests for QueueBroker — transactional outbox pattern."""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from netpalm.backend.core.queue.broker import QueueBroker, TaskNotFoundError, TaskResponse


class TestTaskResponse:
    def test_model_dump(self):
        tid = uuid.uuid4()
        resp = TaskResponse(task_id=tid, status="pending")
        dumped = resp.model_dump()
        assert dumped["task_id"] == str(tid)
        assert dumped["status"] == "pending"
        assert dumped["result"] is None
        assert dumped["error"] is None

    def test_model_dump_with_result(self):
        tid = uuid.uuid4()
        resp = TaskResponse(
            task_id=tid, status="finished", result={"data": "ok"}, error=None
        )
        dumped = resp.model_dump()
        assert dumped["result"] == {"data": "ok"}

    def test_model_dump_with_error(self):
        tid = uuid.uuid4()
        resp = TaskResponse(task_id=tid, status="failed", error="boom")
        dumped = resp.model_dump()
        assert dumped["error"] == "boom"


class TestQueueBroker:
    @pytest.fixture()
    def mock_db(self):
        db = AsyncMock()
        db.add = MagicMock()
        return db

    @pytest.fixture()
    def broker(self, mock_db, mock_settings):
        return QueueBroker(db=mock_db, settings=mock_settings)

    @pytest.mark.asyncio
    async def test_enqueue_task_generates_task_id(self, broker, mock_db):
        resp = await broker.enqueue_task(method="getconfig", kwargs={"host": "10.0.0.1"})
        assert resp.status == "pending"
        assert isinstance(resp.task_id, uuid.UUID)
        mock_db.add.assert_called_once()
        mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_enqueue_task_uses_provided_task_id(self, broker, mock_db):
        tid = uuid.uuid4()
        resp = await broker.enqueue_task(
            method="setconfig", kwargs={"payload": "test"}, task_id=tid
        )
        assert resp.task_id == tid

    @pytest.mark.asyncio
    async def test_enqueue_task_pinned(self, broker, mock_db):
        resp = await broker.enqueue_task(
            method="getconfig",
            kwargs={},
            queue_strategy="pinned",
            pinned_host="switch1",
        )
        assert resp.status == "pending"
        job_record = mock_db.add.call_args[0][0]
        assert job_record.queue_strategy == "pinned"
        assert job_record.pinned_host == "switch1"

    @pytest.mark.asyncio
    async def test_fetch_task_success(self, broker, mock_db):
        tid = uuid.uuid4()
        mock_job = MagicMock()
        mock_job.task_id = tid
        mock_job.status = "finished"
        mock_job.result = {"output": "ok"}
        mock_job.error = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_job
        mock_db.execute.return_value = mock_result

        resp = await broker.fetch_task(str(tid))
        assert resp.task_id == tid
        assert resp.status == "finished"
        assert resp.result == {"output": "ok"}

    @pytest.mark.asyncio
    async def test_fetch_task_not_found(self, broker, mock_db):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(TaskNotFoundError):
            await broker.fetch_task(str(uuid.uuid4()))

    @pytest.mark.asyncio
    async def test_fetch_task_accepts_uuid(self, broker, mock_db):
        tid = uuid.uuid4()
        mock_job = MagicMock()
        mock_job.task_id = tid
        mock_job.status = "pending"
        mock_job.result = None
        mock_job.error = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_job
        mock_db.execute.return_value = mock_result

        resp = await broker.fetch_task(tid)
        assert resp.task_id == tid
