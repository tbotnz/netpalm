"""Tests for NetpalmExecutor — Kafka consumer that executes tasks."""

from __future__ import annotations

import json
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from netpalm.backend.core.executor.executor import (
    NetpalmExecutor,
    _serialize_exception_chain,
)


class TestSerializeExceptionChain:
    def test_single_exception(self):
        exc = ValueError("bad value")
        chain = _serialize_exception_chain(exc)
        assert len(chain) == 1
        assert chain[0]["exception_class"] == "ValueError"
        assert chain[0]["exception_args"] == ["bad value"]

    def test_chained_exceptions(self):
        try:
            try:
                raise ConnectionError("connection lost")
            except ConnectionError as inner:
                raise RuntimeError("operation failed") from inner
        except RuntimeError as outer:
            chain = _serialize_exception_chain(outer)

        assert len(chain) == 2
        # Root cause first (reversed)
        assert chain[0]["exception_class"] == "ConnectionError"
        assert chain[1]["exception_class"] == "RuntimeError"

    def test_implicit_context(self):
        try:
            try:
                raise KeyError("key")
            except KeyError:
                raise ValueError("val")  # noqa: B904
        except ValueError as outer:
            chain = _serialize_exception_chain(outer)

        assert len(chain) == 2
        assert chain[0]["exception_class"] == "KeyError"
        assert chain[1]["exception_class"] == "ValueError"

    def test_no_cycle(self):
        exc = RuntimeError("loop")
        # Manually create a cycle (pathological)
        exc.__cause__ = exc
        chain = _serialize_exception_chain(exc)
        assert len(chain) == 1

    def test_empty_args(self):
        exc = RuntimeError()
        chain = _serialize_exception_chain(exc)
        assert chain[0]["exception_args"] == []


class TestNetpalmExecutor:
    @pytest.fixture()
    def executor_deps(self, mock_settings):
        consumer = AsyncMock()
        producer = AsyncMock()

        db_session = AsyncMock()
        mock_result = MagicMock()
        db_session.execute.return_value = mock_result
        db_factory = MagicMock()
        db_factory.return_value.__aenter__ = AsyncMock(return_value=db_session)
        db_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        driver_registry = MagicMock()
        operation_registry = MagicMock()
        event_registry = MagicMock()
        event_registry.get_topics.return_value = ["netpalm.events.syslog"]

        executor = NetpalmExecutor(
            consumer=consumer,
            producer=producer,
            db_factory=db_factory,
            driver_registry=driver_registry,
            operation_registry=operation_registry,
            event_registry=event_registry,
            settings=mock_settings,
        )
        return {
            "executor": executor,
            "consumer": consumer,
            "producer": producer,
            "db_factory": db_factory,
            "db_session": db_session,
            "mock_result": mock_result,
            "driver_registry": driver_registry,
            "operation_registry": operation_registry,
            "event_registry": event_registry,
        }

    @pytest.mark.asyncio
    async def test_handle_task_success(self, executor_deps):
        deps = executor_deps
        executor = deps["executor"]
        task_id = uuid.uuid4()

        from netpalm.backend.core.models.models import TaskMessage

        msg = TaskMessage(
            task_id=task_id,
            method="getconfig",
            kwargs={"host": "10.0.0.1", "command": "show version"},
        )

        mock_job = MagicMock()
        mock_job.task_id = task_id
        mock_job.status = "pending"
        deps["mock_result"].scalar_one_or_none.return_value = mock_job

        mock_op = MagicMock()
        mock_op.execute.return_value = {"output": "version 1.0"}
        deps["operation_registry"].get.return_value = mock_op

        await executor._handle_task(msg)

        deps["operation_registry"].get.assert_called_once_with("getconfig")
        mock_op.execute.assert_called_once()
        deps["producer"].send.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_handle_task_job_not_found(self, executor_deps):
        deps = executor_deps
        executor = deps["executor"]
        task_id = uuid.uuid4()

        from netpalm.backend.core.models.models import TaskMessage

        msg = TaskMessage(task_id=task_id, method="getconfig", kwargs={})

        deps["mock_result"].scalar_one_or_none.return_value = None

        await executor._handle_task(msg)

        # Should return early without calling operation or producing result
        deps["operation_registry"].get.assert_not_called()
        deps["producer"].send.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_handle_task_operation_failure(self, executor_deps):
        deps = executor_deps
        executor = deps["executor"]
        task_id = uuid.uuid4()

        from netpalm.backend.core.models.models import TaskMessage

        msg = TaskMessage(task_id=task_id, method="getconfig", kwargs={})

        mock_job = MagicMock()
        mock_job.task_id = task_id
        mock_job.status = "pending"
        deps["mock_result"].scalar_one_or_none.return_value = mock_job

        mock_op = MagicMock()
        mock_op.execute.side_effect = RuntimeError("device unreachable")
        deps["operation_registry"].get.return_value = mock_op

        await executor._handle_task(msg)

        # Should still produce result message even on failure
        deps["producer"].send.assert_awaited_once()
        call_kwargs = deps["producer"].send.call_args
        result_bytes = call_kwargs.kwargs.get("value") or call_kwargs[1].get("value") or call_kwargs[0][1]
        result_data = json.loads(result_bytes)
        assert result_data["status"] == "failed"
        assert result_data["error"] is not None
