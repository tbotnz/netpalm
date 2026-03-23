# Implementation Plan: netpalm Modernisation

## Overview

Incremental replacement of the Redis/RQ task queue with Apache Kafka, migration of all persistent state to PostgreSQL via SQLAlchemy async + Alembic, introduction of the transactional outbox pattern, a formal service-instance state machine, event-driven automation via `EventListenerRegistry`, and strict Python typing with Pydantic v2 throughout. All existing external API contracts and southbound driver behaviour are preserved.

## Tasks

- [x] 1. Project scaffolding and dependency updates
  - Remove `rq`, `apscheduler`, and any Redis-queue-related packages from `requirements.txt` / `pyproject.toml`
  - Add `aiokafka`, `sqlalchemy[asyncio]`, `asyncpg`, `alembic`, `pydantic>=2`, `pydantic-settings` dependencies
  - Create `netpalm/scheduler.py` and `netpalm/executor.py` as runnable module entry-points (`python -m netpalm.scheduler`, `python -m netpalm.executor`)
  - Create `alembic/` directory at project root with `alembic.ini` and `alembic/env.py` wired to the async SQLAlchemy engine
  - _Requirements: 14.2, 17.3, 17.4_

- [x] 2. Configuration — NetpalmSettings
  - [x] 2.1 Implement `NetpalmSettings` in `netpalm/backend/core/confload/confload.py`
    - Replace the existing plain-class config with a `pydantic-settings` `BaseSettings` subclass
    - Load from `defaults.json`, then `config.json`, then `NETPALM_*` env vars (priority order)
    - Declare all fields with types: `api_key: SecretStr`, `kafka_bootstrap_servers`, `database_url`, `redis_*`, `scheduler_poll_interval_seconds`, `kafka_events_syslog_topic`, `kafka_events_snmp_topic`, etc.
    - Add `@field_validator("kafka_bootstrap_servers")` that raises `ValueError` if the value is empty or whitespace-only
    - Expose `get_settings()` function suitable for FastAPI `Depends()`
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 13.4_

  - [ ] 2.2 Write property test for NetpalmSettings source priority (Property 1)
    - **Property 1: Configuration source priority**
    - **Validates: Requirements 1.1**

  - [ ] 2.3 Write property test for invalid configuration rejection (Property 2)
    - **Property 2: Invalid configuration is rejected at startup**
    - **Validates: Requirements 1.2**

  - [ ] 2.4 Write property test for api_key SecretStr masking (Property 3)
    - **Property 3: API key is never exposed as plain text**
    - **Validates: Requirements 1.5, 15.3**

- [ ] 3. Database models and Alembic migration
  - [x] 3.1 Implement SQLAlchemy async ORM models in `netpalm/backend/core/models/db_models.py`
    - Define `Base`, `JobRecord`, `ServiceInstanceRecord`, `ServiceInstanceVersionRecord`, `ScheduledJobRecord` exactly as specified in the design
    - Add `UniqueConstraint("service_id", "version")` to `ServiceInstanceVersionRecord`
    - Create async engine factory and `AsyncSession` factory in `netpalm/backend/core/db.py`
    - _Requirements: 14.1, 14.4_

  - [~] 3.2 Generate initial Alembic migration
    - Run `alembic revision --autogenerate -m "initial schema"` to produce the first migration script
    - Verify the generated migration creates all four tables with correct columns, indexes, and constraints
    - _Requirements: 14.2_

  - [~] 3.3 Add `alembic upgrade head` to container startup
    - Update `Dockerfile` / entrypoint scripts so `alembic upgrade head` runs before the application starts
    - _Requirements: 14.3_

- [ ] 4. Checkpoint — database layer
  - Ensure ORM models import cleanly, Alembic migration applies without errors, and async session factory is importable. Ask the user if questions arise.

- [ ] 5. QueueBroker
  - [x] 5.1 Implement `QueueBroker` in `netpalm/backend/core/queue/broker.py`
    - Accept `AsyncSession` and `NetpalmSettings` in `__init__`
    - `enqueue_task()`: INSERT a `JobRecord` with `status=pending`; store `pinned_host` when `queue_strategy=pinned`; return `TaskResponse` immediately — no Kafka calls
    - `fetch_task()`: SELECT `JobRecord` by `task_id`; return `TaskResponse`; raise `TaskNotFoundError` if missing
    - _Requirements: 2.2, 2.3, 2.4, 2.5_

  - [ ] 5.2 Write property test for job submission creates pending record (Property 5)
    - **Property 5: Job submission creates a pending record**
    - **Validates: Requirements 2.2, 2.4**

  - [ ] 5.3 Write property test for QueueBroker never calls Kafka (Property 6)
    - **Property 6: QueueBroker never calls Kafka directly**
    - **Validates: Requirements 2.3**

  - [ ] 5.4 Write property test for pinned strategy persists host (Property 7)
    - **Property 7: Pinned strategy persists host on JobRecord**
    - **Validates: Requirements 2.5**

- [ ] 6. Pydantic v2 request/response models
  - [x] 6.1 Migrate all API request/response models to Pydantic v2 in `netpalm/backend/core/models/`
    - Update `GetConfig`, `SetConfig`, `Script`, `TaskResponse`, `ServiceTaskResponse`, `ServiceInstanceData`, `ServiceVersionSummary` to Pydantic v2 (`model_config`, `model_validator`, etc.)
    - Add `QueueStrategy` enum (`fifo` | `pinned`) and `TaskMessage` / `ResultMessage` Kafka payload models
    - Add `NetpalmEvent` Pydantic model (`source_topic`, `device_host`, `event_type`, `raw`, `data`)
    - _Requirements: 2.1, 17.1_

  - [ ] 6.2 Write property test for invalid request bodies return HTTP 422 (Property 4)
    - **Property 4: Invalid request bodies return HTTP 422**
    - **Validates: Requirements 2.1**

- [ ] 7. ServiceStore and state machine
  - [x] 7.1 Implement `ServiceInstanceState` enum and `VALID_TRANSITIONS` table in `netpalm/backend/core/service/state_machine.py`
    - Define all six states: `deploying`, `deployed`, `updating`, `deleting`, `deleted`, `errored`
    - Define `VALID_TRANSITIONS` dict exactly as specified in the design
    - Define `InvalidStateTransitionError` and `ServiceVersionNotFoundError` exceptions
    - _Requirements: 8.1, 8.2_

  - [ ] 7.2 Write property test for state machine rejects invalid transitions (Property 18)
    - **Property 18: State machine rejects all invalid transitions**
    - **Validates: Requirements 8.1, 8.2**

  - [x] 7.3 Implement `ServiceStore` in `netpalm/backend/core/service/store.py`
    - Implement `create()`, `fetch()`, `transition()`, `update_data()`, `delete()`, `list_all()`
    - Implement `snapshot()`: INSERT `ServiceInstanceVersionRecord`, increment `current_version`, return new version number
    - Implement `rollback()`: read version snapshot (or latest if `to_version=None`), set `state=deploying`, restore `data`, insert `service_rollback` pending `JobRecord`; raise `ServiceVersionNotFoundError` if version missing
    - Call `snapshot()` automatically before every mutating transition (`deploying→deployed`, `deployed→updating`, `updating→deployed`)
    - On `updating→errored` transition, automatically call `rollback()`
    - _Requirements: 7.1, 7.2, 7.3, 8.1, 8.2, 8.3, 8.4, 8.5, 9.1, 9.2, 9.3_

  - [ ] 7.4 Write property test for errored-from-updating triggers rollback (Property 19)
    - **Property 19: Errored-from-updating triggers automatic rollback**
    - **Validates: Requirements 8.3, 8.4**

  - [ ] 7.5 Write property test for snapshot taken before mutating transitions (Property 20)
    - **Property 20: Snapshot is taken before every mutating transition and version increments monotonically**
    - **Validates: Requirements 9.1, 9.2**

  - [ ] 7.6 Write property test for version list ordered descending (Property 21)
    - **Property 21: Version list is ordered descending**
    - **Validates: Requirements 9.4**

- [ ] 8. Checkpoint — service layer
  - Ensure `ServiceStore` and state machine tests pass. Ask the user if questions arise.

- [ ] 9. CacheStore
  - [x] 9.1 Implement `CacheStore` in `netpalm/backend/core/cache/store.py`
    - Wrap `cachelib.RedisCache` with typed `get()`, `set()`, and `poison()` methods
    - `poison(host_port_key)` invalidates all cache entries for the given `host:port` key
    - Ensure no other component imports or uses Redis directly
    - _Requirements: 11.1, 11.3, 11.4_

  - [ ] 9.2 Write property test for cache set/get round-trip (Property 23)
    - **Property 23: Cache set/get round-trip**
    - **Validates: Requirements 11.1**

  - [ ] 9.3 Write property test for cache poison invalidates all entries for a host (Property 24)
    - **Property 24: Cache poison invalidates all entries for a host**
    - **Validates: Requirements 11.3**

- [ ] 10. NetpalmDriver ABC and DriverRegistry
  - [x] 10.1 Implement `NetpalmDriver` ABC in `netpalm/backend/core/driver/netpalm_driver.py`
    - Declare abstract methods `connect()`, `sendcommand()`, `config()`, `logout()` with typed signatures
    - Add `driver_name: str` class attribute
    - _Requirements: 10.1_

  - [x] 10.2 Implement `DriverRegistry` in `netpalm/backend/core/driver/driver_auto_loader.py`
    - Scan the `drivers` directory at startup and auto-load all `NetpalmDriver` subclasses
    - Expose `get(library: str) -> type[NetpalmDriver]`; raise `DriverNotFoundError` if missing
    - _Requirements: 10.2, 10.3, 10.4_

  - [x] 10.3 Update existing southbound drivers to implement the `NetpalmDriver` ABC
    - Update `napalm_drvr.py`, `netmiko_drvr.py`, `ncclient_drvr.py`, `puresnmp_drvr.py`, `restconf.py` to subclass `NetpalmDriver` and implement all abstract methods
    - Preserve all existing driver behaviour
    - _Requirements: 10.5_

- [ ] 11. EventListener ABC and EventListenerRegistry
  - [x] 11.1 Implement `EventListener` ABC in `netpalm/backend/plugins/event_listeners/base.py`
    - Declare `topics: list[str]` class attribute
    - Declare abstract methods `parse(raw: bytes) -> NetpalmEvent | None` and `async on_event(event: NetpalmEvent, manager: NetpalmManager) -> None`
    - _Requirements: 12.7_

  - [x] 11.2 Implement `EventListenerRegistry` in `netpalm/backend/core/events/registry.py`
    - `load()`: scan `event_listeners_dir`, import all `EventListener` subclasses; raise `EventListenerLoadError` if a subclass is missing `topics`, `parse`, or `on_event`
    - Register each listener against each topic in its `topics` list
    - `get_topics()`: return all topics with at least one registered listener
    - `dispatch(topic, raw)`: for each listener on the topic, call `parse(raw)`; if non-None, call `on_event(event, manager)`
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.8_

  - [ ] 11.3 Write property test for registry registers listeners against all declared topics (Property 26)
    - **Property 26: EventListenerRegistry registers listeners against all declared topics**
    - **Validates: Requirements 12.2, 12.8**

  - [ ] 11.4 Write property test for dispatch calls on_event iff parse returns non-None (Property 27)
    - **Property 27: Dispatch calls on_event iff parse returns non-None**
    - **Validates: Requirements 12.4, 12.5, 12.6**

- [ ] 12. NetpalmManager
  - [x] 12.1 Implement `NetpalmManager` in `netpalm/backend/core/manager/netpalm_manager.py`
    - Accept `QueueBroker`, `ServiceStore`, `CacheStore` via constructor injection (no direct Kafka/Redis/DB access)
    - Implement `get_config()`, `set_config()`, `execute_script()`, `fetch_task()`
    - Implement `create_service()`, `get_service()`, `update_service()`, `delete_service()`
    - For `get_config()`: check `CacheStore` first when `redis_cache_enabled=true`; return cached result without enqueuing if hit
    - Remove inheritance from `Rediz`
    - _Requirements: 2.2, 7.1, 7.2, 7.3, 11.2, 17.5_

  - [ ] 12.2 Write property test for cache hit prevents new job enqueue (Property 25)
    - **Property 25: Cache hit prevents new job enqueue**
    - **Validates: Requirements 11.2**

  - [ ] 12.3 Write property test for service creation initialises correct records (Property 16)
    - **Property 16: Service creation initialises correct records**
    - **Validates: Requirements 7.1, 7.4**

  - [ ] 12.4 Write property test for service update and delete trigger correct transitions (Property 17)
    - **Property 17: Service update and delete trigger correct transitions and jobs**
    - **Validates: Requirements 7.2, 7.3**

- [ ] 13. Checkpoint — core layer
  - Ensure all core layer tests pass (QueueBroker, ServiceStore, CacheStore, NetpalmManager). Ask the user if questions arise.

- [ ] 14. Scheduler service
  - [x] 14.1 Implement `Scheduler` in `netpalm/backend/core/scheduler/scheduler.py`
    - Accept `db_factory`, `AIOKafkaProducer`, and `NetpalmSettings` in `__init__`
    - `_relay_pending_jobs()`: SELECT pending `JobRecord` rows in batches; produce `TaskMessage` to the correct Kafka topic via `_resolve_topic()`; UPDATE `status=queued` only after `producer.flush()` succeeds; on Kafka failure log error and leave job as `pending`
    - `_dispatch_scheduled_jobs()`: SELECT `ScheduledJobRecord` rows where `next_run_at <= now() AND enabled=true`; INSERT a new `JobRecord` per due job; UPDATE `last_run_at` and compute new `next_run_at` for `interval` and `cron` triggers; support `date` trigger type
    - `_resolve_topic()`: `fifo` → `kafka_fifo_topic`; `pinned` → `{kafka_pinned_topic_prefix}.{pinned_host}`
    - `run()`: run both loops concurrently with `asyncio.gather`; sleep `scheduler_poll_interval_seconds` between cycles
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3, 4.4, 4.5_

  - [x] 14.2 Implement `netpalm/scheduler.py` entry-point
    - Wire up `AsyncSession` factory, `AIOKafkaProducer`, `NetpalmSettings`, and `Scheduler`; call `scheduler.run()`
    - _Requirements: 3.6_

  - [ ] 14.3 Write property test for outbox relay round-trip (Property 8)
    - **Property 8: Outbox relay round-trip (pending → Kafka → queued)**
    - **Validates: Requirements 3.2, 3.3**

  - [ ] 14.4 Write property test for Kafka failure leaves jobs pending (Property 9)
    - **Property 9: Kafka failure leaves jobs pending**
    - **Validates: Requirements 3.4**

  - [ ] 14.5 Write property test for topic resolution correctness (Property 10)
    - **Property 10: Topic resolution is correct for all strategies**
    - **Validates: Requirements 3.5**

  - [ ] 14.6 Write property test for only due and enabled scheduled jobs are dispatched (Property 11)
    - **Property 11: Only due and enabled scheduled jobs are dispatched**
    - **Validates: Requirements 4.1, 4.2**

  - [ ] 14.7 Write property test for scheduled job next_run_at advances after dispatch (Property 12)
    - **Property 12: Scheduled job next_run_at advances after dispatch**
    - **Validates: Requirements 4.3**

- [ ] 15. Executor service
  - [x] 15.1 Implement `NetpalmExecutor` in `netpalm/backend/core/executor/executor.py`
    - Accept `AIOKafkaConsumer`, `AIOKafkaProducer`, `db_factory`, `DriverRegistry`, `EventListenerRegistry`, and `NetpalmSettings` in `__init__`
    - `run()`: subscribe to topics from `DriverRegistry` + `EventListenerRegistry.get_topics()`; poll loop calling `_handle_task()` for job messages and `EventListenerRegistry.dispatch()` for event messages
    - `_handle_task()`: UPDATE `JobRecord` to `started` + `started_at`; look up driver via `DriverRegistry`; call `driver.connect()` / `driver.sendcommand()` or `driver.config()`; on success UPDATE to `finished` + `result` + `ended_at`; on exception UPDATE to `failed` + `error` + `ended_at`; produce `ResultMessage` to `netpalm.results` in both cases
    - If driver not found in registry: UPDATE `JobRecord` to `failed` with descriptive error
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 10.3, 10.4_

  - [x] 15.2 Implement `netpalm/executor.py` entry-point
    - Wire up consumer, producer, DB factory, `DriverRegistry`, `EventListenerRegistry`, `NetpalmSettings`; call `executor.run()`
    - _Requirements: 5.6_

  - [ ] 15.3 Write property test for executor updates job status through lifecycle (Property 13)
    - **Property 13: Executor updates job status through lifecycle**
    - **Validates: Requirements 5.2, 5.3, 5.4**

  - [ ] 15.4 Write property test for executor produces result to results topic (Property 14)
    - **Property 14: Executor produces result to results topic**
    - **Validates: Requirements 5.5**

  - [ ] 15.5 Write property test for executor selects correct driver from registry (Property 22)
    - **Property 22: Executor selects correct driver from registry**
    - **Validates: Requirements 10.3, 10.4**

- [ ] 16. Checkpoint — scheduler and executor
  - Ensure scheduler and executor tests pass. Ask the user if questions arise.

- [ ] 17. API routes and security
  - [x] 17.1 Update API security middleware in `netpalm/backend/core/security/get_api_key.py`
    - Read `api_key` from `NetpalmSettings` (via `get_settings()` dependency)
    - Return HTTP 401/403 for requests without a valid API key
    - _Requirements: 15.1, 15.2, 15.3_

  - [ ] 17.2 Write property test for unauthenticated requests are rejected (Property 28)
    - **Property 28: Unauthenticated requests are rejected**
    - **Validates: Requirements 15.1, 15.2**

  - [x] 17.3 Update job submission routes (`/getconfig`, `/setconfig`, `/script`)
    - Validate request bodies against Pydantic v2 models; return HTTP 422 on validation failure
    - Call `NetpalmManager.get_config()` / `set_config()` / `execute_script()`; return HTTP 201 with `{status, data.task_id}`
    - _Requirements: 2.1, 2.4_

  - [x] 17.4 Update task result route (`GET /task/{task_id}`)
    - Query `QueueBroker.fetch_task()`; return HTTP 404 if not found; return `status` and `result` fields
    - _Requirements: 6.1, 6.2, 6.3_

  - [ ] 17.5 Write property test for task result retrieval reflects DB state (Property 15)
    - **Property 15: Task result retrieval reflects DB state**
    - **Validates: Requirements 6.1, 6.3**

  - [x] 17.6 Update service lifecycle routes (`/service/*`)
    - `POST /service/{model}` → `NetpalmManager.create_service()` → HTTP 201 with `{service_id, task_id}`
    - `GET /service/{service_id}` → `NetpalmManager.get_service()` → current state and data
    - `PUT /service/{service_id}` → `NetpalmManager.update_service()`
    - `DELETE /service/{service_id}` → `NetpalmManager.delete_service()`
    - `GET /service/{service_id}/versions` → `ServiceStore.list_versions()`
    - `POST /service/{service_id}/rollback` → `ServiceStore.rollback()` with optional `to_version`
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 9.4, 9.5_

- [ ] 18. Remove dead code
  - [x] 18.1 Delete or gut `netpalm/backend/core/redis/rediz.py`
    - Remove the `Rediz` class entirely; redistribute responsibilities to `QueueBroker`, `ServiceStore`, `CacheStore`, and `Scheduler` as already implemented
    - Update all import sites
    - _Requirements: 17.5_

  - [-] 18.2 Remove RQ and APScheduler references
    - Delete any remaining `rq`, `rq_scheduler`, or `apscheduler` imports and usage throughout the codebase
    - _Requirements: 17.3, 17.4_

- [ ] 19. docker-compose and deployment
  - [~] 19.1 Update `docker-compose.yml` (and `docker-compose.dev.yml`) with the new service topology
    - Add `postgres` service (`postgres:16-alpine`) with volume
    - Add `kafka` service (`apache/kafka:3.7.0`) in KRaft mode with the environment variables from the design
    - Add `kafka-ui` service (`ghcr.io/kafbat/kafka-ui:latest`) on port 8080, depending on `kafka`
    - Keep `redis` service for `CacheStore`
    - Add `netpalm-scheduler` service with `command: python -m netpalm.scheduler`, depending on `postgres` and `kafka`
    - Add `netpalm-executor` service with `command: python -m netpalm.executor`, depending on `postgres` and `kafka`
    - Update `netpalm-api-server` to depend on `postgres`, `kafka`, and `redis`
    - Set `NETPALM_DATABASE_URL`, `NETPALM_KAFKA_BOOTSTRAP_SERVERS`, `NETPALM_REDIS_SERVER` env vars on each service
    - _Requirements: 13.1, 13.2, 13.3, 13.5, 16.1, 16.2, 16.3, 16.4, 16.5, 16.6_

- [ ] 20. Final checkpoint — full integration
  - Ensure all tests pass, all imports resolve, `alembic upgrade head` applies cleanly, and the docker-compose topology is consistent. Ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at each architectural layer
- Property tests validate universal correctness properties; unit tests validate specific examples and edge cases
- The `Rediz` class removal (task 18) should be done after all replacement components are in place
