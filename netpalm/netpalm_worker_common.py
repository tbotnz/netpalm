"""
netpalm_worker_common.py — DEPRECATED.

The Redis broadcast queue, RQ workers, and APScheduler have been removed.
Worker coordination is now handled by:
  - netpalm.scheduler  (Scheduler service — outbox relay + scheduled jobs)
  - netpalm.executor   (NetpalmExecutor — Kafka consumer)

This file is kept as a tombstone. It will be removed in a future release.
"""

from __future__ import annotations

import logging

log = logging.getLogger(__name__)


def start_broadcast_listener_process() -> None:
    """No-op — broadcast listener has been removed."""
    log.debug("start_broadcast_listener_process: no-op (broadcast listener removed)")
