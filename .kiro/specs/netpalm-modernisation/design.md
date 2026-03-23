# Design Document: netpalm Modernisation

## Overview

netpalm is an open API platform for network devices that abstracts southbound drivers (napalm, netmiko, ncclient, puresnmp, restconf) behind a unified REST API. The codebase has grown organically and needs a full modernisation pass: strict Python typing throughout, Pydantic v2 models as the single source of truth for all data contracts, removal of dead code, and a cleaner layered architecture that separates concerns more clearly.

The modernisation replaces the Redis/RQ task queue with Apache Kafka as the message bus, enabling event-driven task dispatch, durable topic-based routing, and a clear integration point for future event sources (syslog listeners, SNMP trap receivers) that can publish directly to Kafka topics. Redis is retained only as a response cache store (via cachelib). Job records, job metadata, and service instance state are persisted in PostgreSQL via SQLAlchemy (async) with Alembic managing schema migrations. Service instances are modelled as a formal state machine backed by the database, with valid transitions enforced at the application layer. All existing external API contracts and southbound driver behaviour are preserved.

A key reliability pattern is the **transactional outbox**: when a job is submitted via the API, it is written to PostgreSQL first (status `pending`), and a separate `Scheduler` service continuously polls for pending jobs and publishes them to Kafka. This guarantees no jobs are silently dropped if Kafka is temporarily unavailable at submission time. The `Scheduler` also replaces APScheduler entirely: it polls the `scheduled_jobs` table for due jobs and enqueues them as new `JobRecord` rows.

## Architecture

```mermaid
graph TD
    subgraph API["api-server (FastAPI)"]
        R[Routes / Endpoints]
        SEC[Security - API Key]
    end

    subgraph Core["Core Layer"]
        MGR[NetpalmManager]
        CFG[Config - pydantic-settings]
        QB[QueueBroker]
    end

    subgraph DB["Persistence (PostgreSQL)"]
        JT[jobs table]
        ST[service_instances table]
        SJT[scheduled_jobs table]
    end

    subgraph Sched["Scheduler Service"]
        REL[Scheduler - outbox relay + scheduled job dispatch]
    end

    subgraph Kafka["Message Bus (Apache Kafka)"]
        KT_FIFO[Topic: netpalm.jobs.fifo]
        KT_PIN[Topic: netpalm.jobs.pinned.{host}]
        KT_RES[Topic: netpalm.results]
        KT_EVT[Topic: netpalm.events.syslog / netpalm.events.snmp-trap]
        KUI[Kafbat UI]
    end

    subgraph Executors["Executor Layer"]
        EXEC[Task Executors - Kafka Consumers]
        DRV[Driver Registry]
        ELR[EventListenerRegistry]
    end

    subgraph Drivers["Southbound Drivers"]
        NM[netmiko]
        NA[napalm]
        NC[ncclient]
        SN[puresnmp]
        RC[restconf]
    end

    subgraph Cache["Cache Layer"]
        REDIS[Redis - CacheStore only]
    end

    subgraph Future["Future Event Sources (planned — publish side only)"]
        SL[Syslog Listener]
        SNMPT[SNMP Trap Receiver]
    end

    R --> SEC
    R --> MGR
    MGR --> QB
    QB --> JT
    JT --> REL
    SJT --> REL
    REL --> KT_FIFO
    REL --> KT_PIN
    EXEC --> KT_FIFO & KT_PIN
    EXEC --> KT_RES
    EXEC --> JT
    EXEC --> DRV
    EXEC --> ELR
    ELR -->|consumes| KT_EVT
    ELR -->|calls| MGR
    DRV --> NM & NA & NC & SN & RC
    CFG --> MGR & QB & REL
    QB --> REDIS
    KUI -.->|observes| Kafka
    SL -.->|publishes| KT_EVT
    SNMPT -.->|publishes| KT_EVT
    KT_RES --> JT
```

### Key Architectural Decisions

- **RQ removed entirely.** Executors are plain Kafka consumers; no RQ worker process, no RQ job registry.
- **APScheduler removed entirely.** The `Scheduler` service polls the `scheduled_jobs` PostgreSQL table directly. No Redis job store, no APScheduler library.
- **Redis scope reduced.** Redis is used only by `CacheStore` (cachelib `RedisCache`). No queues, no service store, no pinned-worker registry in Redis.
- **PostgreSQL is the system of record.** All job lifecycle state, service instance state, and scheduled job definitions live in the DB. Kafka is a transport, not a store.
- **Outbox relay decouples api-server from Kafka.** The api-server never calls `producer.produce()` directly; it only writes to the DB. The `Scheduler` handles Kafka publishing.
- **Kafbat UI** (`ghcr.io/kafbat/kafka-ui`) replaces any Redis queue UI for observing Kafka topics and consumer group lag.
- **Kafka runs in KRaft mode.** No Zookeeper dependency. The `apache/kafka` image is used (official Apache Kafka image). KRaft mode simplifies deployment and is the production-recommended mode as of Kafka 3.3+.

## Sequence Diagrams

### getconfig request flow (DB-first / outbox pattern)

```mermaid
sequenceDiagram
    participant C as Client
    participant API as api-server
    participant MGR as NetpalmManager
    participant QB as QueueBroker
    participant DB as PostgreSQL
    participant SCH as Scheduler
    participant KT as Kafka: netpalm.jobs.fifo
    participant E as executor (Consumer)
    participant D as Driver
    participant KR as Kafka: netpalm.results

    C->>API: POST /getconfig {library, connection_args, command}
    API->>API: validate request (Pydantic v2 model)
    API->>MGR: get_config(model)
    MGR->>QB: enqueue_task("getconfig", task_id, kwargs)
    QB->>DB: INSERT jobs (task_id, status=pending, payload)
    QB-->>MGR: task_id
    MGR-->>API: TaskResponse {task_id, status=pending}
    API-->>C: 201 {status, data.task_id}

    Note over SCH: Scheduler polls continuously
    SCH->>DB: SELECT * FROM jobs WHERE status='pending' LIMIT N
    SCH->>KT: produce(key=task_id, value=TaskMessage)
    SCH->>DB: UPDATE jobs SET status='queued' WHERE task_id=...

    E->>KT: poll() → TaskMessage
    E->>DB: UPDATE jobs SET status='started', started_at=now()
    E->>D: driver.connect()
    E->>D: driver.sendcommand(session, commands)
    D-->>E: result dict
    E->>DB: UPDATE jobs SET status='finished', result=..., ended_at=now()
    E->>KR: produce(key=task_id, value=ResultMessage)

    C->>API: GET /task/{task_id}
    API->>DB: SELECT * FROM jobs WHERE task_id=...
    DB-->>API: job row
    API-->>C: 200 {status, data}
```

### Scheduled job dispatch flow

```mermaid
sequenceDiagram
    participant SCH as Scheduler
    participant DB as PostgreSQL
    participant KT as Kafka: netpalm.jobs.fifo
    participant E as executor (Consumer)

    Note over SCH: Scheduler polls scheduled_jobs continuously
    SCH->>DB: SELECT * FROM scheduled_jobs WHERE next_run_at <= now() AND enabled=true
    SCH->>DB: INSERT jobs (method, payload, status=pending) for each due job
    SCH->>DB: UPDATE scheduled_jobs SET last_run_at=now(), next_run_at=<next> WHERE job_id=...
    SCH->>DB: SELECT * FROM jobs WHERE status='pending' LIMIT N
    SCH->>KT: produce(key=task_id, value=TaskMessage)
    SCH->>DB: UPDATE jobs SET status='queued' WHERE task_id=...

    E->>KT: poll() → TaskMessage
    E->>DB: UPDATE jobs SET status='started', started_at=now()
    E->>DB: UPDATE jobs SET status='finished', result=..., ended_at=now()
```

### Service instance lifecycle (state machine)

```mermaid
sequenceDiagram
    participant C as Client
    participant API as api-server
    participant MGR as NetpalmManager
    participant DB as PostgreSQL
    participant SCH as Scheduler
    participant E as executor

    C->>API: POST /service/{model}
    API->>MGR: create_service(model, request)
    MGR->>DB: INSERT service_instances (state=deploying)
    MGR->>DB: INSERT jobs (method=service_create, status=pending)
    MGR-->>API: {service_id, task_id}
    API-->>C: 201 {service_id, task_id}

    SCH->>DB: poll pending jobs
    SCH->>E: publish to Kafka
    E->>E: execute service_create procedure
    E->>DB: UPDATE service_instances SET state=deployed
    E->>DB: UPDATE jobs SET status=finished

    C->>API: PUT /service/{service_id}
    API->>MGR: update_service(service_id, request)
    MGR->>DB: UPDATE service_instances SET state=updating (validate deployed→updating)
    MGR->>DB: INSERT jobs (method=service_update, status=pending)
    MGR-->>API: {service_id, task_id}
    SCH->>E: publish to Kafka
    E->>E: execute service_update procedure
    E->>DB: UPDATE service_instances SET state=deployed (or errored on failure)
    E->>DB: UPDATE jobs SET status=finished

    C->>API: DELETE /service/{service_id}
    API->>MGR: delete_service(service_id)
    MGR->>DB: UPDATE service_instances SET state=deleting (validate transition)
    MGR->>DB: INSERT jobs (method=service_delete, status=pending)
    SCH->>E: publish to Kafka
    E->>DB: UPDATE service_instances SET state=deleted
```

### Event-driven flow

```mermaid
sequenceDiagram
    participant SRC as Syslog/SNMP Trap Source (future)
    participant LST as Event Publisher (future service)
    participant KE as Kafka: netpalm.events.syslog
    participant ELR as EventListenerRegistry
    participant LI as EventListener subclass
    participant MGR as NetpalmManager

    SRC->>LST: raw syslog line / SNMP trap PDU
    LST->>LST: parse → NetpalmEvent model
    LST->>KE: produce(key=device_host, value=NetpalmEvent)

    Note over ELR: Executor consumer loop polls registered topics
    ELR->>KE: poll() → raw bytes
    ELR->>ELR: registry.get(topic) → listener class
    ELR->>LI: listener.handle(raw)
    LI->>LI: parse(raw) → NetpalmEvent | None
    alt event is not None
        LI->>MGR: on_event(event, manager)
        MGR->>MGR: get_config() / set_config() / create_service()
    else parse returned None
        LI-->>ELR: discard (no action)
    end
```

## Components and Interfaces

### Config (pydantic-settings)

**Purpose**: Single source of truth for all application configuration, loaded from JSON files and environment variables.

**Current problem**: Plain class with manual attribute assignment and no type validation.

**Target interface**:
```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr, field_validator

class NetpalmSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="NETPALM_", extra="ignore")

    listen_ip: str = "0.0.0.0"
    listen_port: int = 9000
    api_key: SecretStr

    # Kafka
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_fifo_topic: str = "netpalm.jobs.fifo"
    kafka_pinned_topic_prefix: str = "netpalm.jobs.pinned"
    kafka_results_topic: str = "netpalm.results"
    kafka_events_syslog_topic: str = "netpalm.events.syslog"
    kafka_events_snmp_topic: str = "netpalm.events.snmp-trap"
    kafka_consumer_group: str = "netpalm-workers"

    # PostgreSQL
    database_url: str = "postgresql+asyncpg://netpalm:netpalm@localhost:5432/netpalm"

    # Redis (cache only)
    redis_server: str = "localhost"
    redis_port: int = 6379
    redis_key: SecretStr = SecretStr("")
    redis_tls_enabled: bool = False
    redis_cache_enabled: bool = False
    redis_cache_default_timeout: int = 300
    redis_cache_key_prefix: str = "netpalm"

    # Scheduler
    scheduler_poll_interval_seconds: int = 5

    drivers: str = "netpalm/backend/plugins/drivers/"
    event_listeners_dir: str = "netpalm/backend/plugins/event_listeners/"

    @field_validator("kafka_bootstrap_servers")
    @classmethod
    def ensure_non_empty_bootstrap(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("kafka_bootstrap_servers must not be empty")
        return v
```

**Responsibilities**:
- Load config from `defaults.json`, `config.json`, then `NETPALM_*` env vars (priority order)
- Validate all values at startup — fail fast on misconfiguration
- Expose a single `get_settings()` function for FastAPI dependency injection

---

### QueueBroker

**Purpose**: Translates `enqueue_task` calls into DB writes (outbox pattern). Does not interact with Kafka directly. Replaces the task-dispatch responsibilities of the old `Rediz` class.

**Current problem**: `Rediz` mixed queue management, service CRUD, worker control, and caching into one 780-line class.

**Target interface**:
```python
class QueueBroker:
    """Writes jobs to the DB. The Scheduler handles Kafka publishing."""

    def __init__(self, db: AsyncSession, settings: NetpalmSettings) -> None: ...

    async def enqueue_task(
        self,
        method: str,
        task_id: str,
        kwargs: dict[str, Any],
        queue_strategy: QueueStrategy,
        pinned_host: str | None = None,
    ) -> TaskResponse:
        """
        INSERT a job row with status=pending.
        Returns immediately with task_id — does NOT wait for Kafka publish.
        """
        ...

    async def fetch_task(self, task_id: str) -> TaskResponse:
        """SELECT job row from DB and return as TaskResponse."""
        ...
```

**Responsibilities**:
- Write job records to PostgreSQL with `status=pending`
- Return `TaskResponse` immediately (non-blocking)
- No Kafka producer calls — that is the Scheduler's job

---

### Scheduler

**Purpose**: Two responsibilities running concurrently in the same process:
1. **Outbox relay** — continuously polls the `jobs` table for `pending` jobs and publishes them to the appropriate Kafka topic, then marks them `queued`.
2. **Scheduled job runner** — polls the `scheduled_jobs` table for jobs whose `next_run_at <= now()`, inserts a new `JobRecord` with `status=pending` for each due job, and updates `next_run_at` for recurring triggers.

Replaces both the old `OutboxRelay` class and APScheduler entirely. No Redis job store, no APScheduler library.

**Target interface**:
```python
class Scheduler:
    """
    Two responsibilities:
    1. Outbox relay: poll jobs WHERE status='pending', publish to Kafka, mark 'queued'.
    2. Scheduled job runner: poll scheduled_jobs WHERE next_run_at <= now() AND enabled=True,
       insert a new job row (status=pending), update next_run_at for recurring triggers.
    """

    def __init__(
        self,
        db_factory: Callable[[], AsyncSession],
        producer: AIOKafkaProducer,
        settings: NetpalmSettings,
    ) -> None: ...

    async def run(self) -> None:
        """Main loop: runs both _relay_pending_jobs and _dispatch_scheduled_jobs concurrently."""
        ...

    async def _relay_pending_jobs(self) -> int:
        """Fetch pending jobs, publish to Kafka, mark queued. Returns count published."""
        ...

    async def _dispatch_scheduled_jobs(self) -> int:
        """Find due scheduled jobs, insert job rows, update next_run_at. Returns count dispatched."""
        ...

    def _resolve_topic(self, job: JobRecord) -> str:
        """fifo → kafka_fifo_topic, pinned → kafka_pinned_topic_prefix.{host}"""
        ...
```

**Responsibilities**:
- Poll `jobs` table for `status='pending'` rows in batches; produce `TaskMessage` to the correct Kafka topic; update `status='queued'` only after `producer.flush()` succeeds
- Poll `scheduled_jobs` table for `next_run_at <= now() AND enabled=True`; insert a new `JobRecord` per due job; compute and persist the next `next_run_at` for interval/cron triggers; set `last_run_at`
- On Kafka failure: log error, leave job as `pending` for retry on next poll cycle
- Runs as a separate process/container (`python -m netpalm.scheduler`)

---

### ServiceStore

**Purpose**: CRUD for service instances, backed by PostgreSQL. Enforces state machine transitions.

**Current problem**: Service instances stored as raw JSON blobs in Redis with no state machine enforcement.

**Target interface**:
```python
class ServiceStore:
    """Service instance persistence with state machine enforcement."""

    def __init__(self, db: AsyncSession) -> None: ...

    async def create(self, service_id: str, model: str, data: dict[str, Any]) -> ServiceInstanceData:
        """INSERT service_instances with state=deploying."""
        ...

    async def fetch(self, service_id: str) -> ServiceInstanceData:
        """SELECT service instance; raises ServiceNotFoundError if missing."""
        ...

    async def transition(self, service_id: str, new_state: ServiceInstanceState) -> None:
        """
        Validate transition is allowed, then UPDATE state.
        Raises InvalidStateTransitionError if transition is not permitted.
        """
        ...

    async def update_data(self, service_id: str, data: dict[str, Any]) -> ServiceInstanceData:
        """
        Transition deployed → updating, persist new data, then enqueue update job.
        Raises InvalidStateTransitionError if instance is not in 'deployed' state.
        """
        ...

    async def delete(self, service_id: str) -> None:
        """Transition to 'deleting', then mark 'deleted' after executor confirms."""
        ...

    async def list_all(self) -> list[ServiceInstanceData]:
        """SELECT all non-deleted service instances."""
        ...

    async def snapshot(self, service_id: str) -> int:
        """
        Write current state+data to service_instance_versions, increment version.
        Called automatically before every state transition that mutates data
        (deploying→deployed, deployed→updating, updating→deployed).
        Returns the new version number.
        """
        ...

    async def rollback(self, service_id: str, to_version: int | None = None) -> ServiceInstanceData:
        """
        Restore service instance state and data from a previous version snapshot.
        If to_version is None, rolls back to the most recent previous version.
        Transitions current state → deploying before applying the rollback payload,
        then enqueues a service_rollback job to re-apply the historical config to the device.
        Raises ServiceVersionNotFoundError if to_version does not exist.
        """
        ...

    async def list_versions(self, service_id: str) -> list[ServiceVersionSummary]:
        """Return all version snapshots for a service instance, ordered by version desc."""
        ...
```

**Valid state transitions** (enforced by `transition()`):

```
deploying → deployed          (deploy succeeded)
deploying → errored           (deploy failed)
deployed  → updating          (update initiated)
updating  → deployed          (update succeeded)
updating  → errored           (update failed)
deployed  → deleting          (delete initiated)
deleting  → deleted           (delete complete)
errored   → deploying         (redeploy/retry)
```

Any other transition raises `InvalidStateTransitionError`.

The `updating` state is new — it covers in-place service reconfiguration without tearing down and recreating the instance. The `update_data()` method on `ServiceStore` triggers the `deployed → updating` transition before enqueuing the update job.

When a transition fails (executor reports `errored`), `ServiceStore` automatically calls `rollback()` to restore the last known-good version. The rollback enqueues a `service_rollback` job that re-applies the previous `data` payload to the device:

```
Executor fails service_update
→ Executor calls ServiceStore.transition(service_id, errored)
→ ServiceStore detects errored transition, calls rollback(service_id)
→ rollback() reads previous version snapshot
→ rollback() sets state=deploying, data=<previous snapshot data>
→ rollback() inserts jobs (method=service_rollback, status=pending)
→ Scheduler picks up job, publishes to Kafka
→ Executor re-applies previous config to device
→ Executor calls ServiceStore.transition(service_id, deployed)
```

---

### CacheStore

**Purpose**: Wraps cachelib `RedisCache` with a typed interface. Redis is retained exclusively for this component.

**Unchanged from current design** — no modifications required.

```python
class CacheStore:
    """Redis-backed response cache (cachelib). Redis scope is limited to this class."""

    def get(self, key: str) -> Any | None: ...
    def set(self, key: str, value: Any, ttl: int) -> None: ...
    def poison(self, host_port_key: str) -> bool:
        """Invalidate all cache entries for a given host:port."""
        ...
```

---

### NetpalmManager

**Purpose**: Orchestration layer — translates typed request models into DB-backed job records via `QueueBroker`, and reads results from the DB.

**Current problem**: Inherits from `Rediz` (tight coupling); mixes orchestration with queue mechanics.

**Target interface**:
```python
class NetpalmManager:
    def __init__(
        self,
        broker: QueueBroker,
        service_store: ServiceStore,
        cache: CacheStore,
    ) -> None: ...

    async def get_config(self, request: GetConfig) -> TaskResponse: ...
    async def set_config(self, request: SetConfig) -> TaskResponse: ...
    async def execute_script(self, request: Script) -> TaskResponse: ...
    async def fetch_task(self, task_id: str) -> TaskResponse: ...

    async def create_service(self, model: str, request: BaseModel) -> ServiceTaskResponse: ...
    async def get_service(self, service_id: str) -> ServiceInstanceData: ...
    async def update_service(self, service_id: str, request: BaseModel) -> ServiceTaskResponse: ...
    async def delete_service(self, service_id: str) -> TaskResponse: ...
```

**Responsibilities**:
- Accept Pydantic v2 models, call `broker.enqueue_task()`, return typed responses
- No direct Kafka, Redis, or raw DB access — delegates to injected dependencies

---

### NetpalmExecutor (Kafka Consumer)

**Purpose**: Consumes `TaskMessage` records from Kafka topics, executes the appropriate driver call, and writes results back to PostgreSQL (and optionally to `netpalm.results` topic).

**Target interface**:
```python
class NetpalmExecutor:
    def __init__(
        self,
        consumer: AIOKafkaConsumer,
        producer: AIOKafkaProducer,
        db_factory: Callable[[], AsyncSession],
        driver_map: DriverMap,
        settings: NetpalmSettings,
    ) -> None: ...

    async def run(self) -> None:
        """Main consume loop. Runs until cancelled."""
        ...

    async def _handle_task(self, msg: TaskMessage) -> None:
        """Execute driver call, write result to DB and results topic."""
        ...
```

---

### NetpalmDriver (Abstract Base)

**Purpose**: Protocol/ABC defining the southbound driver contract. Unchanged from current modernisation design.

```python
from abc import ABC, abstractmethod
from typing import Any

class NetpalmDriver(ABC):
    driver_name: str

    @abstractmethod
    def connect(self) -> Any: ...

    @abstractmethod
    def sendcommand(self, session: Any, command: list[str]) -> dict[str, Any]: ...

    @abstractmethod
    def config(self, session: Any, command: str | list[str], **kwargs: Any) -> dict[str, Any]: ...

    @abstractmethod
    def logout(self, session: Any) -> None: ...
```

---

### EventListener (Abstract Base)

**Purpose**: ABC for user-defined event listeners. Users subclass this, implement `parse()` and `on_event()`, drop the file into the `event_listeners_dir` plugin directory, and the `EventListenerRegistry` auto-discovers and registers it at startup.

```python
from abc import ABC, abstractmethod
from typing import Any

class NetpalmEvent(BaseModel):
    """Parsed event produced by an EventListener."""
    source_topic: str
    device_host: str | None
    event_type: str
    raw: bytes
    data: dict[str, Any]

class EventListener(ABC):
    """
    ABC for user-defined event listeners.
    Users subclass this, implement parse() and on_event(), drop the file into
    the event_listeners_dir plugin directory, and the EventListenerRegistry
    auto-discovers and registers it at startup.
    """

    # Subclasses declare which Kafka topic(s) they subscribe to
    topics: list[str]

    @abstractmethod
    def parse(self, raw: bytes) -> NetpalmEvent | None:
        """
        Parse raw Kafka message bytes into a NetpalmEvent.
        Return None to discard the message (no action taken).
        """

    @abstractmethod
    async def on_event(self, event: NetpalmEvent, manager: "NetpalmManager") -> None:
        """
        React to a parsed event. Use manager to schedule tasks:
            await manager.get_config(...)
            await manager.set_config(...)
            await manager.create_service(...)
        """
```

**Responsibilities**:
- Declare which Kafka topics to subscribe to via the `topics` class attribute
- Parse raw bytes into a typed `NetpalmEvent` (or return `None` to discard)
- React to events by calling `NetpalmManager` methods

---

### EventListenerRegistry

**Purpose**: Discovers `EventListener` subclasses from `event_listeners_dir` at startup. Maintains a `topic → [listener, ...]` mapping. Runs as part of the executor process — subscribes to all registered topics and dispatches incoming messages to the appropriate listeners.

```python
class EventListenerRegistry:
    """
    Discovers EventListener subclasses from event_listeners_dir at startup.
    Maintains a topic → [listener, ...] mapping.
    Runs as part of the executor process — subscribes to all registered topics
    and dispatches incoming messages to the appropriate listeners.
    """

    def __init__(self, manager: NetpalmManager, settings: NetpalmSettings) -> None: ...

    def load(self) -> None:
        """
        Scan event_listeners_dir, import all EventListener subclasses,
        register each against its declared topics.
        Raises EventListenerLoadError if a subclass is missing required attributes.
        """
        ...

    def get_topics(self) -> list[str]:
        """Return all topics that have at least one registered listener."""
        ...

    async def dispatch(self, topic: str, raw: bytes) -> None:
        """
        For each listener registered on topic:
          event = listener.parse(raw)
          if event: await listener.on_event(event, self.manager)
        """
        ...
```

**Responsibilities**:
- Scan `event_listeners_dir` on startup and import all `EventListener` subclasses
- Register each listener against its declared `topics`
- Expose `get_topics()` so the executor can subscribe to the correct Kafka topics
- Dispatch raw Kafka messages to all matching listeners via `dispatch()`

---

## Data Models

### ServiceInstanceState (updated enum)

```python
from enum import Enum

class ServiceInstanceState(str, Enum):
    deploying = "deploying"
    deployed  = "deployed"
    updating  = "updating"   # NEW: in-place update in progress
    deleting  = "deleting"
    deleted   = "deleted"
    errored   = "errored"
```

### State Machine Transition Table

```python
VALID_TRANSITIONS: dict[ServiceInstanceState, set[ServiceInstanceState]] = {
    ServiceInstanceState.deploying: {
        ServiceInstanceState.deployed,
        ServiceInstanceState.errored,
    },
    ServiceInstanceState.deployed: {
        ServiceInstanceState.updating,   # update initiated
        ServiceInstanceState.deleting,   # delete initiated
        ServiceInstanceState.errored,
    },
    ServiceInstanceState.updating: {
        ServiceInstanceState.deployed,   # update succeeded
        ServiceInstanceState.errored,    # update failed
    },
    ServiceInstanceState.deleting: {
        ServiceInstanceState.deleted,
    },
    ServiceInstanceState.errored: {
        ServiceInstanceState.deploying,  # redeploy/retry
    },
    ServiceInstanceState.deleted: set(),  # terminal state
}
```

### ServiceVersionSummary

```python
class ServiceVersionSummary(BaseModel):
    version_id: uuid.UUID
    service_id: uuid.UUID
    version: int
    state: str
    created_at: datetime
```

---

## Database

### Rationale

PostgreSQL is the recommended persistence layer. It is widely understood, has mature async drivers (`asyncpg`), and integrates cleanly with SQLAlchemy async. High availability is straightforward to achieve:

- **Self-hosted HA**: [Patroni](https://github.com/patroni/patroni) + etcd/Consul provides automatic primary election and failover with minimal operational overhead.
- **Managed cloud**: AWS RDS Multi-AZ, Google Cloud SQL HA, Azure Database for PostgreSQL — all provide HA out of the box.
- **Alternative — CockroachDB**: A distributed SQL database with built-in HA (no separate HA tooling needed). It speaks the PostgreSQL wire protocol, so the SQLAlchemy models and migrations work unchanged. Recommended if operators want simpler HA without running Patroni.

### SQLAlchemy ORM Models

```python
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class JobRecord(Base):
    __tablename__ = "jobs"

    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    method: Mapped[str] = mapped_column(String(64), nullable=False)
    queue_strategy: Mapped[str] = mapped_column(String(16), nullable=False)
    pinned_host: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="pending", index=True
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    result: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # status values: pending | queued | started | finished | failed


class ServiceInstanceRecord(Base):
    __tablename__ = "service_instances"

    service_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    service_model: Mapped[str] = mapped_column(String(255), nullable=False)
    state: Mapped[str] = mapped_column(
        String(16), nullable=False, default="deploying", index=True
    )
    data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    current_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # state values: deploying | deployed | updating | deleting | deleted | errored


class ServiceInstanceVersionRecord(Base):
    __tablename__ = "service_instance_versions"

    version_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("service_instances.service_id"), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)  # monotonically increasing per service_id
    state: Mapped[str] = mapped_column(String(16), nullable=False)  # state at time of snapshot
    data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    # UniqueConstraint("service_id", "version")


class ScheduledJobRecord(Base):
    __tablename__ = "scheduled_jobs"

    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    method: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    trigger: Mapped[str] = mapped_column(String(16), nullable=False)  # "interval" | "cron" | "date"
    trigger_args: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    next_run_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

### Schema Migrations

Alembic manages all schema changes. The `alembic/` directory lives at the project root. Migrations are applied at container startup via `alembic upgrade head` before the application starts.

---

## Deployment

### docker-compose (development)

Key services for local development:

```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: netpalm
      POSTGRES_PASSWORD: netpalm
      POSTGRES_DB: netpalm
    ports: ["5432:5432"]
    volumes: [postgres_data:/var/lib/postgresql/data]

  kafka:
    image: apache/kafka:3.7.0
    container_name: kafka
    ports:
      - "9092:9092"
    environment:
      KAFKA_NODE_ID: 1
      KAFKA_PROCESS_ROLES: broker,controller
      KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,CONTROLLER:PLAINTEXT
      KAFKA_CONTROLLER_QUORUM_VOTERS: 1@kafka:9093
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: "true"
      KAFKA_LOG_DIRS: /var/lib/kafka/data
    volumes:
      - kafka_data:/var/lib/kafka/data

  kafka-ui:
    image: ghcr.io/kafbat/kafka-ui:latest
    depends_on: [kafka]
    ports: ["8080:8080"]
    environment:
      KAFKA_CLUSTERS_0_NAME: local
      KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS: kafka:9092

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  netpalm-api-server:
    build: .
    depends_on: [postgres, kafka, redis]
    environment:
      NETPALM_DATABASE_URL: postgresql+asyncpg://netpalm:netpalm@postgres:5432/netpalm
      NETPALM_KAFKA_BOOTSTRAP_SERVERS: kafka:9092
      NETPALM_REDIS_SERVER: redis
    ports: ["9000:9000"]

  netpalm-scheduler:
    build: .
    command: python -m netpalm.scheduler
    depends_on: [postgres, kafka]
    environment:
      NETPALM_DATABASE_URL: postgresql+asyncpg://netpalm:netpalm@postgres:5432/netpalm
      NETPALM_KAFKA_BOOTSTRAP_SERVERS: kafka:9092

  netpalm-executor:
    build: .
    command: python -m netpalm.executor
    depends_on: [postgres, kafka]
    environment:
      NETPALM_DATABASE_URL: postgresql+asyncpg://netpalm:netpalm@postgres:5432/netpalm
      NETPALM_KAFKA_BOOTSTRAP_SERVERS: kafka:9092

volumes:
  postgres_data:
  kafka_data:
```

Kafbat UI is available at `http://localhost:8080` and provides topic browsing, consumer group lag monitoring, and message inspection.

---

## Event-Driven Automation

The `EventListener` ABC and `EventListenerRegistry` ship in this release. Users can write and deploy custom `EventListener` subclasses today by placing them in `event_listeners_dir`. The registry auto-discovers them at executor startup.

The syslog publisher service and SNMP trap receiver remain planned future services (publish side only):

| Topic | Publisher | Consumer |
|---|---|---|
| `netpalm.events.syslog` | Future syslog listener service (planned) | `EventListenerRegistry` (ships now) |
| `netpalm.events.snmp-trap` | Future SNMP trap receiver service (planned) | `EventListenerRegistry` (ships now) |

`NetpalmSettings` exposes `kafka_events_syslog_topic` and `kafka_events_snmp_topic` so topics are configurable without code changes.

### Example: User-Defined EventListener

```python
# netpalm/backend/plugins/event_listeners/syslog_interface_down.py

class SyslogInterfaceDownListener(EventListener):
    topics = ["netpalm.events.syslog"]

    def parse(self, raw: bytes) -> NetpalmEvent | None:
        text = raw.decode()
        if "Interface" not in text or "down" not in text.lower():
            return None
        host = _extract_host(text)
        return NetpalmEvent(
            source_topic="netpalm.events.syslog",
            device_host=host,
            event_type="interface_down",
            raw=raw,
            data={"message": text},
        )

    async def on_event(self, event: NetpalmEvent, manager: NetpalmManager) -> None:
        await manager.get_config(GetConfig(
            library=LibraryName.netmiko,
            connection_args={"host": event.device_host, ...},
            command="show interfaces",
        ))
```


---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Configuration source priority

*For any* set of configuration values defined in multiple sources (defaults.json, config.json, environment variables), the value from the highest-priority source (env vars > config.json > defaults.json) SHALL be the one present in the resulting NetpalmSettings instance.

**Validates: Requirements 1.1**

---

### Property 2: Invalid configuration is rejected at startup

*For any* configuration dict that contains at least one field with an invalid value (wrong type, out-of-range, or constraint violation), instantiating NetpalmSettings SHALL raise a Pydantic ValidationError.

**Validates: Requirements 1.2**

---

### Property 3: API key is never exposed as plain text

*For any* secret string used as the `api_key`, converting the NetpalmSettings instance to a string, dict, or JSON representation SHALL NOT contain the raw secret value.

**Validates: Requirements 1.5, 15.3**

---

### Property 4: Invalid request bodies return HTTP 422

*For any* request body that fails Pydantic v2 model validation for a job submission endpoint, the API_Server SHALL return HTTP 422 and SHALL NOT create a JobRecord in the database.

**Validates: Requirements 2.1**

---

### Property 5: Job submission creates a pending record

*For any* valid job request (getconfig, setconfig, or script), calling `QueueBroker.enqueue_task()` SHALL insert exactly one JobRecord with `status=pending` into PostgreSQL, and the returned `TaskResponse.task_id` SHALL match the inserted row's `task_id`.

**Validates: Requirements 2.2, 2.4**

---

### Property 6: QueueBroker never calls Kafka directly

*For any* call to `QueueBroker.enqueue_task()`, no method on the Kafka producer SHALL be invoked during that call.

**Validates: Requirements 2.3**

---

### Property 7: Pinned strategy persists host on JobRecord

*For any* job submitted with `QueueStrategy.pinned` and a non-empty `pinned_host`, the resulting JobRecord SHALL have `queue_strategy=pinned` and `pinned_host` equal to the submitted value.

**Validates: Requirements 2.5**

---

### Property 8: Outbox relay round-trip (pending → Kafka → queued)

*For any* set of JobRecords with `status=pending`, after one successful `_relay_pending_jobs()` cycle, each job SHALL have been produced to the correct Kafka topic AND its status SHALL be updated to `queued`. No job SHALL be marked `queued` before its Kafka produce call succeeds.

**Validates: Requirements 3.2, 3.3**

---

### Property 9: Kafka failure leaves jobs pending

*For any* pending JobRecord, if the Kafka producer raises an exception during `_relay_pending_jobs()`, the JobRecord SHALL remain with `status=pending` after the cycle completes.

**Validates: Requirements 3.4**

---

### Property 10: Topic resolution is correct for all strategies

*For any* JobRecord with `queue_strategy=fifo`, the resolved Kafka topic SHALL equal `settings.kafka_fifo_topic`. *For any* JobRecord with `queue_strategy=pinned` and `pinned_host=H`, the resolved topic SHALL equal `f"{settings.kafka_pinned_topic_prefix}.{H}"`.

**Validates: Requirements 3.5**

---

### Property 11: Only due and enabled scheduled jobs are dispatched

*For any* set of ScheduledJobRecords, after one `_dispatch_scheduled_jobs()` cycle, a new pending JobRecord SHALL be created if and only if the ScheduledJobRecord has `next_run_at <= now()` AND `enabled=true`. Records with `next_run_at > now()` or `enabled=false` SHALL NOT produce a new JobRecord.

**Validates: Requirements 4.1, 4.2**

---

### Property 12: Scheduled job next_run_at advances after dispatch

*For any* ScheduledJobRecord with trigger type `interval` or `cron` that is dispatched, after the dispatch cycle `last_run_at` SHALL be set to a non-null value and `next_run_at` SHALL be strictly greater than the previous `next_run_at`.

**Validates: Requirements 4.3**

---

### Property 13: Executor updates job status through lifecycle

*For any* TaskMessage consumed by the Executor, the corresponding JobRecord SHALL transition through `started` (with non-null `started_at`) and then to either `finished` (with non-null `result` and `ended_at`) on success, or `failed` (with non-null `error` and `ended_at`) on driver exception.

**Validates: Requirements 5.2, 5.3, 5.4**

---

### Property 14: Executor produces result to results topic

*For any* TaskMessage that the Executor processes to completion (success or failure), a ResultMessage SHALL be produced to the `netpalm.results` Kafka topic.

**Validates: Requirements 5.5**

---

### Property 15: Task result retrieval reflects DB state

*For any* JobRecord in any status, a `GET /task/{task_id}` request SHALL return a response whose `status` field matches the current `JobRecord.status` and whose `result` field matches `JobRecord.result`.

**Validates: Requirements 6.1, 6.3**

---

### Property 16: Service creation initialises correct records

*For any* valid service creation request, `NetpalmManager.create_service()` SHALL insert a ServiceInstanceRecord with `state=deploying` and a JobRecord with `method=service_create` and `status=pending`, and the API SHALL return HTTP 201 with both `service_id` and `task_id`.

**Validates: Requirements 7.1, 7.4**

---

### Property 17: Service update and delete trigger correct transitions and jobs

*For any* ServiceInstanceRecord in `state=deployed`, calling `update_service()` SHALL transition the state to `updating` and insert a `service_update` pending JobRecord; calling `delete_service()` SHALL transition the state to `deleting` and insert a `service_delete` pending JobRecord.

**Validates: Requirements 7.2, 7.3**

---

### Property 18: State machine rejects all invalid transitions

*For any* (current_state, new_state) pair that is NOT in the VALID_TRANSITIONS table, calling `ServiceStore.transition()` SHALL raise `InvalidStateTransitionError` and the ServiceInstanceRecord SHALL remain unchanged.

**Validates: Requirements 8.1, 8.2**

---

### Property 19: Errored-from-updating triggers automatic rollback

*For any* ServiceInstanceRecord in `state=updating`, transitioning to `errored` SHALL automatically invoke `rollback()`, which SHALL set `state=deploying`, restore `data` from the most recent version snapshot, and insert a `service_rollback` pending JobRecord.

**Validates: Requirements 8.3, 8.4**

---

### Property 20: Snapshot is taken before every mutating transition and version increments monotonically

*For any* ServiceInstanceRecord undergoing a mutating transition (`deploying→deployed`, `deployed→updating`, `updating→deployed`), a ServiceInstanceVersionRecord SHALL be inserted before the transition is applied, and the `current_version` on the ServiceInstanceRecord SHALL be strictly greater than it was before the call.

**Validates: Requirements 9.1, 9.2**

---

### Property 21: Version list is ordered descending

*For any* service instance with N version snapshots, `ServiceStore.list_versions()` SHALL return exactly N records ordered by `version` descending (highest version first).

**Validates: Requirements 9.4**

---

### Property 22: Executor selects correct driver from registry

*For any* TaskMessage whose `library` field matches a driver registered in the DriverRegistry, the Executor SHALL invoke that driver's methods. *For any* TaskMessage whose `library` field does not match any registered driver, the Executor SHALL update the JobRecord to `status=failed` with a descriptive error.

**Validates: Requirements 10.3, 10.4**

---

### Property 23: Cache set/get round-trip

*For any* key-value pair stored via `CacheStore.set()`, a subsequent `CacheStore.get()` with the same key SHALL return an equivalent value (before TTL expiry).

**Validates: Requirements 11.1**

---

### Property 24: Cache poison invalidates all entries for a host

*For any* set of cache entries sharing a `host:port` key prefix, calling `CacheStore.poison(host_port_key)` SHALL result in `CacheStore.get()` returning `None` for all previously cached entries under that key.

**Validates: Requirements 11.3**

---

### Property 25: Cache hit prevents new job enqueue

*For any* request that produces a cache hit in CacheStore (when `redis_cache_enabled=true`), the API_Server SHALL return the cached result and SHALL NOT insert a new JobRecord into the database.

**Validates: Requirements 11.2**

---

### Property 26: EventListenerRegistry registers listeners against all declared topics

*For any* EventListener subclass with a `topics` list of length N, after `EventListenerRegistry.load()`, `get_topics()` SHALL include all N topics, and `dispatch()` SHALL invoke that listener's `parse()` for messages on each of those topics.

**Validates: Requirements 12.2, 12.8**

---

### Property 27: Dispatch calls on_event iff parse returns non-None

*For any* raw Kafka message dispatched to a registered listener, `on_event()` SHALL be called if and only if `parse()` returns a non-None `NetpalmEvent`. If `parse()` returns `None`, `on_event()` SHALL NOT be called.

**Validates: Requirements 12.4, 12.5, 12.6**

---

### Property 28: Unauthenticated requests are rejected

*For any* request to any API endpoint that does not include a valid API key, the API_Server SHALL return HTTP 401 or HTTP 403 and SHALL NOT process the request.

**Validates: Requirements 15.1, 15.2**
