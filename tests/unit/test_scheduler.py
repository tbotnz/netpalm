"""Tests for Scheduler — outbox relay + scheduled job dispatcher."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from netpalm.backend.core.scheduler.scheduler import Scheduler, _compute_next_run


class TestComputeNextRun:
    """Test the _compute_next_run helper function."""

    def _make_sched(self, trigger, trigger_args=None, enabled=True):
        sched = MagicMock()
        sched.trigger = trigger
        sched.trigger_args = trigger_args or {}
        sched.enabled = enabled
        return sched

    def test_interval_seconds(self):
        sched = self._make_sched("interval", {"seconds": 30})
        now = datetime(2026, 1, 1, tzinfo=UTC)
        result = _compute_next_run(sched, now)
        assert result == now + timedelta(seconds=30)

    def test_interval_minutes(self):
        sched = self._make_sched("interval", {"minutes": 5})
        now = datetime(2026, 1, 1, tzinfo=UTC)
        result = _compute_next_run(sched, now)
        assert result == now + timedelta(minutes=5)

    def test_interval_hours(self):
        sched = self._make_sched("interval", {"hours": 2})
        now = datetime(2026, 1, 1, tzinfo=UTC)
        result = _compute_next_run(sched, now)
        assert result == now + timedelta(hours=2)

    def test_interval_days(self):
        sched = self._make_sched("interval", {"days": 1})
        now = datetime(2026, 1, 1, tzinfo=UTC)
        result = _compute_next_run(sched, now)
        assert result == now + timedelta(days=1)

    def test_interval_weeks(self):
        sched = self._make_sched("interval", {"weeks": 1})
        now = datetime(2026, 1, 1, tzinfo=UTC)
        result = _compute_next_run(sched, now)
        assert result == now + timedelta(weeks=1)

    def test_interval_combined(self):
        sched = self._make_sched("interval", {"hours": 1, "minutes": 30})
        now = datetime(2026, 1, 1, tzinfo=UTC)
        result = _compute_next_run(sched, now)
        assert result == now + timedelta(hours=1, minutes=30)

    def test_interval_zero_fallback(self):
        sched = self._make_sched("interval", {})
        now = datetime(2026, 1, 1, tzinfo=UTC)
        result = _compute_next_run(sched, now)
        assert result == now + timedelta(seconds=60)

    def test_cron_advances_one_minute(self):
        sched = self._make_sched("cron", {"minute": "*/5"})
        now = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
        result = _compute_next_run(sched, now)
        assert result == now + timedelta(minutes=1)

    def test_date_trigger_disables(self):
        sched = self._make_sched("date", {})
        now = datetime(2026, 1, 1, tzinfo=UTC)
        result = _compute_next_run(sched, now)
        assert result == now
        assert sched.enabled is False


class TestScheduler:
    @pytest.fixture()
    def scheduler_deps(self, mock_settings):
        db_session = AsyncMock()
        db_factory = MagicMock()
        db_factory.return_value.__aenter__ = AsyncMock(return_value=db_session)
        db_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        producer = AsyncMock()

        scheduler = Scheduler(
            db_factory=db_factory,
            producer=producer,
            settings=mock_settings,
        )
        return {
            "scheduler": scheduler,
            "db_session": db_session,
            "producer": producer,
        }

    async def test_relay_pending_jobs_empty(self, scheduler_deps):
        deps = scheduler_deps
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        deps["db_session"].execute.return_value = mock_result

        count = await deps["scheduler"]._relay_pending_jobs()
        assert count == 0
        deps["producer"].send.assert_not_awaited()

    async def test_relay_pending_jobs_publishes(self, scheduler_deps):
        deps = scheduler_deps

        job = MagicMock()
        job.task_id = uuid.uuid4()
        job.method = "getconfig"
        job.payload = {"host": "10.0.0.1"}
        job.queue_strategy = "fifo"
        job.pinned_host = None
        job.status = "pending"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [job]
        deps["db_session"].execute.return_value = mock_result

        count = await deps["scheduler"]._relay_pending_jobs()
        assert count == 1
        assert job.status == "queued"
        deps["producer"].send.assert_awaited_once()
        deps["db_session"].commit.assert_awaited()

    async def test_relay_pending_jobs_kafka_error(self, scheduler_deps):
        from aiokafka.errors import KafkaError

        deps = scheduler_deps

        job = MagicMock()
        job.task_id = uuid.uuid4()
        job.method = "getconfig"
        job.payload = {}
        job.queue_strategy = "fifo"
        job.pinned_host = None
        job.status = "pending"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [job]
        deps["db_session"].execute.return_value = mock_result

        deps["producer"].send.side_effect = KafkaError("broker down")

        count = await deps["scheduler"]._relay_pending_jobs()
        assert count == 0
        assert job.status == "pending"  # status should NOT change

    async def test_dispatch_scheduled_jobs_empty(self, scheduler_deps):
        deps = scheduler_deps
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        deps["db_session"].execute.return_value = mock_result

        count = await deps["scheduler"]._dispatch_scheduled_jobs()
        assert count == 0

    async def test_dispatch_scheduled_jobs_creates_job(self, scheduler_deps):
        deps = scheduler_deps

        sched = MagicMock()
        sched.job_id = uuid.uuid4()
        sched.name = "test-schedule"
        sched.method = "getconfig"
        sched.payload = {"host": "10.0.0.1"}
        sched.trigger = "interval"
        sched.trigger_args = {"seconds": 60}
        sched.next_run_at = datetime.now(UTC) - timedelta(seconds=10)
        sched.enabled = True

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sched]
        deps["db_session"].execute.return_value = mock_result

        count = await deps["scheduler"]._dispatch_scheduled_jobs()
        assert count == 1
        deps["db_session"].add.assert_called_once()
        deps["db_session"].commit.assert_awaited()

    def test_resolve_topic_fifo(self, mock_settings):
        scheduler = Scheduler(
            db_factory=MagicMock(),
            producer=AsyncMock(),
            settings=mock_settings,
        )
        job = MagicMock()
        job.queue_strategy = "fifo"
        job.pinned_host = None
        assert scheduler._resolve_topic(job) == "netpalm.jobs.fifo"

    def test_resolve_topic_always_fifo(self, mock_settings):
        """_resolve_topic always returns the fifo topic (single executor model)."""
        scheduler = Scheduler(
            db_factory=MagicMock(),
            producer=AsyncMock(),
            settings=mock_settings,
        )
        job = MagicMock()
        job.queue_strategy = "pinned"
        job.pinned_host = "switch1"
        assert scheduler._resolve_topic(job) == "netpalm.jobs.fifo"
