"""
schedule.py — DEPRECATED.

APScheduler has been removed. Scheduled jobs are now managed via the
`scheduled_jobs` PostgreSQL table and dispatched by the Scheduler service.

See:
  - netpalm.backend.core.models.db_models.ScheduledJobRecord
  - netpalm.backend.core.scheduler.scheduler.Scheduler
"""

raise ImportError(
    "netpalm.backend.core.schedule.schedule (APScheduler) is no longer available. "
    "Use the ScheduledJobRecord DB model and the Scheduler service instead."
)
