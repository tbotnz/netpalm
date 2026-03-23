"""
rediz.py — DEPRECATED.

The Rediz class has been removed as part of the netpalm modernisation.

Responsibilities have been redistributed:
  - Job queuing        → netpalm.backend.core.queue.broker.QueueBroker
  - Service instances  → netpalm.backend.core.service.store.ServiceStore
  - Response cache     → netpalm.backend.core.cache.store.CacheStore
  - Kafka publishing   → netpalm.backend.core.scheduler.scheduler.Scheduler
  - Task execution     → netpalm.backend.core.executor.executor.NetpalmExecutor

This file is kept as a tombstone to aid migration. It will be removed in a future release.
"""

raise ImportError(
    "netpalm.backend.core.redis.rediz is no longer available. See the module docstring for the replacement components."
)
