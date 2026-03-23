# Requirements Document

## Introduction

This document captures the formal requirements for the netpalm modernisation project. The modernisation replaces the Redis/RQ task queue with Apache Kafka as the message bus, migrates all persistent state from Redis to PostgreSQL (via SQLAlchemy async + Alembic), introduces a transactional outbox pattern for reliable job dispatch, enforces a formal service-instance state machine, adds an event-driven automation layer, and applies strict Python typing with Pydantic v2 models throughout. All existing external API contracts and southbound driver behaviour are preserved.

## Glossary

- **API_Server**: The FastAPI application that exposes the REST API to clients.
- **QueueBroker**: The component that writes job records to PostgreSQL (outbox pattern). Does not interact with Kafka directly.
- **Scheduler**: The background service that relays pending jobs from PostgreSQL to Kafka and dispatches scheduled jobs.
- **Executor**: A Kafka consumer process that executes driver calls and writes results back to PostgreSQL.
- **NetpalmManager**: The orchestration layer that translates typed request models into DB-backed job records via QueueBroker.
- **ServiceStore**: The component responsible for CRUD operations on service instances, backed by PostgreSQL, with state machine enforcement.
- **CacheStore**: The Redis-backed response cache (cachelib RedisCache). Redis is used exclusively by this component.
- **DriverRegistry**: The component that auto-discovers and loads southbound driver plugins at startup.
- **EventListenerRegistry**: The component that auto-discovers EventListener subclasses and dispatches Kafka event messages to them.
- **EventListener**: An abstract base class that users subclass to react to Kafka event messages.
- **NetpalmDriver**: The abstract base class defining the southbound driver contract.
- **NetpalmSettings**: The Pydantic-settings configuration model, the single source of truth for all application configuration.
- **JobRecord**: A PostgreSQL row representing a single job (pending → queued → started → finished/failed).
- **ServiceInstanceRecord**: A PostgreSQL row representing a service instance and its current state.
- **ScheduledJobRecord**: A PostgreSQL row representing a recurring or one-shot scheduled job definition.
- **ServiceInstanceVersionRecord**: A PostgreSQL row representing a point-in-time snapshot of a service instance.
- **TaskMessage**: The Kafka message payload produced by the Scheduler and consumed by the Executor.
- **NetpalmEvent**: A Pydantic model representing a parsed event produced by an EventListener.
- **OutboxRelay**: The sub-loop within the Scheduler that polls pending jobs and publishes them to Kafka.
- **QueueStrategy**: An enum value (`fifo` or `pinned`) that determines which Kafka topic a job is routed to.
- **KRaft**: Apache Kafka's built-in consensus mechanism (no Zookeeper required).

---

## Requirements

### Requirement 1: Configuration Management

**User Story:** As a system operator, I want all application configuration to be validated at startup from a single source of truth, so that misconfiguration is caught immediately before the application accepts traffic.

#### Acceptance Criteria

1. THE NetpalmSettings SHALL load configuration values from `defaults.json`, then `config.json`, then `NETPALM_*` environment variables, with later sources overriding earlier ones.
2. WHEN the application starts, THE NetpalmSettings SHALL validate all configuration values using Pydantic v2 field validators and fail fast with a descriptive error if any value is invalid.
3. IF `kafka_bootstrap_servers` is empty or whitespace-only, THEN THE NetpalmSettings SHALL raise a `ValueError` with a descriptive message during startup validation.
4. THE API_Server SHALL expose a `get_settings()` function suitable for FastAPI dependency injection that returns the singleton NetpalmSettings instance.
5. THE NetpalmSettings SHALL expose `api_key` as a `SecretStr` field so that the secret value is not logged or serialised in plain text.

---

### Requirement 2: Job Submission via Outbox Pattern

**User Story:** As a client, I want to submit network jobs via the REST API and receive an immediate acknowledgement, so that I am not blocked waiting for the job to complete.

#### Acceptance Criteria

1. WHEN a client submits a valid job request (getconfig, setconfig, or script), THE API_Server SHALL validate the request body against the corresponding Pydantic v2 model and return HTTP 422 if validation fails.
2. WHEN a valid job request is received, THE QueueBroker SHALL insert a `JobRecord` row into PostgreSQL with `status=pending` and return a `TaskResponse` containing the `task_id` immediately.
3. THE QueueBroker SHALL NOT call any Kafka producer method directly; all Kafka publishing is delegated to the Scheduler.
4. WHEN a job is inserted, THE API_Server SHALL return HTTP 201 with a response body containing `status` and `data.task_id`.
5. THE QueueBroker SHALL support `QueueStrategy` values of `fifo` and `pinned`; for `pinned` strategy, a `pinned_host` value SHALL be stored on the `JobRecord`.

---

### Requirement 3: Scheduler — Outbox Relay

**User Story:** As a system operator, I want pending jobs to be reliably published to Kafka even if Kafka was temporarily unavailable at submission time, so that no jobs are silently dropped.

#### Acceptance Criteria

1. WHILE the Scheduler is running, THE Scheduler SHALL continuously poll the `jobs` table for rows with `status=pending` at an interval defined by `scheduler_poll_interval_seconds`.
2. WHEN pending jobs are found, THE Scheduler SHALL produce a `TaskMessage` to the correct Kafka topic for each job before updating the job status.
3. WHEN a `TaskMessage` has been successfully flushed to Kafka, THE Scheduler SHALL update the corresponding `JobRecord` status to `queued`.
4. IF Kafka publishing fails for a job, THEN THE Scheduler SHALL log the error and leave the `JobRecord` with `status=pending` so it is retried on the next poll cycle.
5. THE Scheduler SHALL resolve the Kafka topic for a job as follows: `fifo` strategy → `kafka_fifo_topic`; `pinned` strategy → `{kafka_pinned_topic_prefix}.{pinned_host}`.
6. THE Scheduler SHALL run as a separate process (`python -m netpalm.scheduler`) independently of the API_Server.

---

### Requirement 4: Scheduler — Scheduled Job Dispatch

**User Story:** As a network operator, I want to define recurring or one-shot scheduled jobs, so that routine network tasks run automatically without manual intervention.

#### Acceptance Criteria

1. WHILE the Scheduler is running, THE Scheduler SHALL continuously poll the `scheduled_jobs` table for rows where `next_run_at <= now()` AND `enabled=true`.
2. WHEN a due scheduled job is found, THE Scheduler SHALL insert a new `JobRecord` with `status=pending` for that job.
3. WHEN a scheduled job has been dispatched, THE Scheduler SHALL update `last_run_at` to the current time and compute and persist the new `next_run_at` for `interval` and `cron` trigger types.
4. THE Scheduler SHALL support trigger types `interval`, `cron`, and `date` as stored in the `ScheduledJobRecord.trigger` field.
5. THE Scheduler SHALL replace APScheduler entirely; no APScheduler library dependency SHALL remain in the codebase.

---

### Requirement 5: Task Execution via Kafka Consumer

**User Story:** As a system operator, I want jobs to be executed by dedicated consumer processes that are decoupled from the API server, so that the API server remains responsive under load.

#### Acceptance Criteria

1. WHEN the Executor starts, THE Executor SHALL subscribe to the Kafka topics it is configured to consume from (fifo and/or pinned topics).
2. WHEN a `TaskMessage` is consumed from Kafka, THE Executor SHALL update the corresponding `JobRecord` to `status=started` and record `started_at`.
3. WHEN a driver call completes successfully, THE Executor SHALL update the `JobRecord` to `status=finished`, store the result in `JobRecord.result`, and record `ended_at`.
4. IF a driver call raises an exception, THEN THE Executor SHALL update the `JobRecord` to `status=failed`, store the error message in `JobRecord.error`, and record `ended_at`.
5. WHEN a job result is written to the database, THE Executor SHALL also produce a `ResultMessage` to the `netpalm.results` Kafka topic.
6. THE Executor SHALL run as a separate process (`python -m netpalm.executor`) independently of the API_Server and Scheduler.
7. THE Executor SHALL NOT use RQ (Redis Queue) or any RQ worker process; all task dispatch is via Kafka.

---

### Requirement 6: Task Result Retrieval

**User Story:** As a client, I want to poll for the status and result of a submitted job, so that I can retrieve the output once execution is complete.

#### Acceptance Criteria

1. WHEN a client sends `GET /task/{task_id}`, THE API_Server SHALL query the `jobs` table in PostgreSQL and return the current `status` and `result` fields.
2. IF no `JobRecord` exists for the given `task_id`, THEN THE API_Server SHALL return HTTP 404.
3. THE API_Server SHALL return job status values of `pending`, `queued`, `started`, `finished`, or `failed` as defined by the `JobRecord` status field.

---

### Requirement 7: Service Instance Lifecycle Management

**User Story:** As a network operator, I want to create, update, and delete service instances through the API, so that I can manage complex multi-step network configurations as a single logical unit.

#### Acceptance Criteria

1. WHEN a client sends `POST /service/{model}`, THE API_Server SHALL call `NetpalmManager.create_service()`, which SHALL insert a `ServiceInstanceRecord` with `state=deploying` and a `JobRecord` with `method=service_create` and `status=pending`.
2. WHEN a client sends `PUT /service/{service_id}`, THE API_Server SHALL call `NetpalmManager.update_service()`, which SHALL transition the service instance from `deployed` to `updating` and insert a `JobRecord` with `method=service_update` and `status=pending`.
3. WHEN a client sends `DELETE /service/{service_id}`, THE API_Server SHALL call `NetpalmManager.delete_service()`, which SHALL transition the service instance from `deployed` to `deleting` and insert a `JobRecord` with `method=service_delete` and `status=pending`.
4. THE API_Server SHALL return HTTP 201 with `service_id` and `task_id` for service creation requests.
5. WHEN a client sends `GET /service/{service_id}`, THE API_Server SHALL return the current state and data of the service instance.

---

### Requirement 8: Service Instance State Machine

**User Story:** As a system operator, I want service instance state transitions to be strictly enforced, so that services cannot enter invalid states due to concurrent operations or bugs.

#### Acceptance Criteria

1. THE ServiceStore SHALL enforce the following valid state transitions and reject all others with an `InvalidStateTransitionError`:
   - `deploying` → `deployed` or `errored`
   - `deployed` → `updating`, `deleting`, or `errored`
   - `updating` → `deployed` or `errored`
   - `deleting` → `deleted`
   - `errored` → `deploying`
   - `deleted` → (no valid transitions; terminal state)
2. IF a requested state transition is not in the valid transition table, THEN THE ServiceStore SHALL raise `InvalidStateTransitionError` without modifying the `ServiceInstanceRecord`.
3. WHEN a service instance transitions to `errored` from `updating`, THE ServiceStore SHALL automatically invoke `rollback()` to restore the last known-good version snapshot.
4. WHEN `rollback()` is invoked, THE ServiceStore SHALL set the service instance state to `deploying`, restore the `data` field from the selected version snapshot, and insert a `JobRecord` with `method=service_rollback` and `status=pending`.
5. IF `rollback()` is called with a `to_version` that does not exist, THEN THE ServiceStore SHALL raise `ServiceVersionNotFoundError`.

---

### Requirement 9: Service Instance Versioning

**User Story:** As a network operator, I want service instance state to be snapshotted before each mutating transition, so that I can roll back to a previous known-good configuration if an update fails.

#### Acceptance Criteria

1. WHEN a service instance undergoes a mutating state transition (`deploying→deployed`, `deployed→updating`, `updating→deployed`), THE ServiceStore SHALL call `snapshot()` before applying the transition.
2. WHEN `snapshot()` is called, THE ServiceStore SHALL insert a `ServiceInstanceVersionRecord` with the current `state` and `data`, increment `current_version`, and return the new version number.
3. THE ServiceStore SHALL store version snapshots in the `service_instance_versions` table with a unique constraint on `(service_id, version)`.
4. WHEN a client sends `GET /service/{service_id}/versions`, THE API_Server SHALL return all version snapshots for that service instance ordered by version descending.
5. WHEN a client sends `POST /service/{service_id}/rollback` with an optional `to_version`, THE API_Server SHALL invoke `ServiceStore.rollback()` and return the resulting `ServiceInstanceData`.

---

### Requirement 10: Southbound Driver Abstraction

**User Story:** As a developer, I want all southbound drivers to implement a common interface, so that the executor can invoke any driver uniformly without driver-specific branching.

#### Acceptance Criteria

1. THE NetpalmDriver ABC SHALL declare abstract methods `connect()`, `sendcommand()`, `config()`, and `logout()` that all concrete driver implementations must implement.
2. THE DriverRegistry SHALL scan the `drivers` directory at startup and auto-load all `NetpalmDriver` subclasses found there.
3. WHEN the Executor receives a `TaskMessage`, THE Executor SHALL look up the appropriate driver from the DriverRegistry using the `library` field of the task payload.
4. IF a requested driver is not found in the DriverRegistry, THEN THE Executor SHALL update the `JobRecord` to `status=failed` with a descriptive error message.
5. THE system SHALL preserve the existing southbound driver behaviour for napalm, netmiko, ncclient, puresnmp, and restconf drivers.

---

### Requirement 11: Response Caching

**User Story:** As a network operator, I want repeated identical queries to be served from cache, so that device load is reduced for frequently polled data.

#### Acceptance Criteria

1. WHERE `redis_cache_enabled` is `true`, THE CacheStore SHALL cache job results in Redis using cachelib `RedisCache` with a TTL of `redis_cache_default_timeout` seconds.
2. WHERE `redis_cache_enabled` is `true`, WHEN a cache hit occurs for a request, THE API_Server SHALL return the cached result without enqueuing a new job.
3. THE CacheStore SHALL expose a `poison(host_port_key)` method that invalidates all cache entries for a given `host:port` key.
4. THE CacheStore SHALL be the only component that interacts with Redis; no other component SHALL use Redis for queuing, state storage, or worker coordination.

---

### Requirement 12: Event-Driven Automation

**User Story:** As a network operator, I want to define custom event listeners that react to Kafka events and trigger network operations automatically, so that I can automate responses to network events without manual intervention.

#### Acceptance Criteria

1. THE EventListenerRegistry SHALL scan `event_listeners_dir` at executor startup and import all `EventListener` subclasses found there.
2. WHEN an `EventListener` subclass is loaded, THE EventListenerRegistry SHALL register it against each topic declared in its `topics` class attribute.
3. IF an `EventListener` subclass is missing required attributes (`topics`, `parse`, `on_event`), THEN THE EventListenerRegistry SHALL raise `EventListenerLoadError` and abort startup.
4. WHEN a Kafka message arrives on a registered topic, THE EventListenerRegistry SHALL call `listener.parse(raw)` for each listener registered on that topic.
5. WHEN `listener.parse(raw)` returns a `NetpalmEvent`, THE EventListenerRegistry SHALL call `listener.on_event(event, manager)`.
6. WHEN `listener.parse(raw)` returns `None`, THE EventListenerRegistry SHALL discard the message and take no further action.
7. THE EventListener ABC SHALL declare abstract methods `parse(raw: bytes) -> NetpalmEvent | None` and `on_event(event: NetpalmEvent, manager: NetpalmManager) -> None` that subclasses must implement.
8. THE EventListenerRegistry SHALL expose a `get_topics()` method that returns all topics with at least one registered listener, so the Executor can subscribe to the correct Kafka topics.

---

### Requirement 13: Message Bus Infrastructure (Kafka)

**User Story:** As a system operator, I want the message bus to be reliable and observable, so that I can monitor job throughput and diagnose consumer lag.

#### Acceptance Criteria

1. THE system SHALL use Apache Kafka running in KRaft mode (no Zookeeper dependency) as the message bus.
2. THE system SHALL define the following Kafka topics: `netpalm.jobs.fifo`, `netpalm.jobs.pinned.{host}`, `netpalm.results`, `netpalm.events.syslog`, and `netpalm.events.snmp-trap`.
3. THE system SHALL deploy Kafbat UI (`ghcr.io/kafbat/kafka-ui`) as the Kafka observability interface, replacing any Redis queue UI.
4. THE NetpalmSettings SHALL expose `kafka_events_syslog_topic` and `kafka_events_snmp_topic` as configurable fields so topic names can be changed without code modifications.
5. THE system SHALL use the `apache/kafka` official image for the Kafka broker in the docker-compose deployment.

---

### Requirement 14: Database Persistence and Migrations

**User Story:** As a system operator, I want all job, service, and schedule state to be persisted in PostgreSQL with managed schema migrations, so that state survives process restarts and can be evolved safely.

#### Acceptance Criteria

1. THE system SHALL persist all `JobRecord`, `ServiceInstanceRecord`, `ServiceInstanceVersionRecord`, and `ScheduledJobRecord` data in PostgreSQL using SQLAlchemy async ORM models.
2. THE system SHALL use Alembic to manage all schema migrations; the `alembic/` directory SHALL live at the project root.
3. WHEN a container starts, THE system SHALL run `alembic upgrade head` before the application begins accepting requests or consuming messages.
4. THE system SHALL use `asyncpg` as the async PostgreSQL driver, configured via the `database_url` setting with the `postgresql+asyncpg://` scheme.
5. THE system SHALL NOT store job records, service instance state, or scheduled job definitions in Redis.

---

### Requirement 15: API Security

**User Story:** As a system operator, I want all API endpoints to require a valid API key, so that unauthorised clients cannot submit jobs or read results.

#### Acceptance Criteria

1. THE API_Server SHALL require a valid API key on all endpoints, validated by the security middleware.
2. IF a request is received without a valid API key, THEN THE API_Server SHALL return HTTP 401 or HTTP 403.
3. THE NetpalmSettings SHALL store the `api_key` as a `SecretStr` field to prevent accidental logging of the secret value.

---

### Requirement 16: Deployment and Containerisation

**User Story:** As a developer, I want a docker-compose configuration that starts all required services locally, so that I can develop and test the full system without manual infrastructure setup.

#### Acceptance Criteria

1. THE docker-compose configuration SHALL define services for `postgres`, `kafka`, `kafka-ui`, `redis`, `netpalm-api-server`, `netpalm-scheduler`, and `netpalm-executor`.
2. THE `netpalm-api-server` service SHALL depend on `postgres`, `kafka`, and `redis` being available before starting.
3. THE `netpalm-scheduler` and `netpalm-executor` services SHALL depend on `postgres` and `kafka` being available before starting.
4. THE `netpalm-scheduler` service SHALL be started with the command `python -m netpalm.scheduler`.
5. THE `netpalm-executor` service SHALL be started with the command `python -m netpalm.executor`.
6. THE Kafbat UI service SHALL be accessible at `http://localhost:8080` in the local development environment.

---

### Requirement 17: Code Quality and Type Safety

**User Story:** As a developer, I want the codebase to use strict Python typing and Pydantic v2 models as the single source of truth for all data contracts, so that type errors are caught at development time rather than at runtime.

#### Acceptance Criteria

1. THE system SHALL use Pydantic v2 models for all request/response data contracts exposed by the API_Server.
2. THE system SHALL use `pydantic-settings` `BaseSettings` for all application configuration (NetpalmSettings).
3. THE system SHALL remove all RQ (Redis Queue) library dependencies from the codebase.
4. THE system SHALL remove all APScheduler library dependencies from the codebase.
5. THE `Rediz` class SHALL be removed and its responsibilities redistributed to `QueueBroker`, `ServiceStore`, `CacheStore`, and `Scheduler` as defined in the design.
