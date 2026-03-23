<p align="center">
   <img src="/static/images/netpalm.png" width="300" />
   <br/>
   <strong>The Open API Platform for Network Devices</strong>
   <br/><br/>
   <img src="https://github.com/tbotnz/netpalm/workflows/tests/badge.svg" />
   <img src="https://img.shields.io/github/stars/tbotnz/netpalm" />
   <img src="https://img.shields.io/github/license/tbotnz/netpalm" />
</p>

netpalm is a REST API broker for your network. Point it at any device — SSH, Telnet, NETCONF, RESTCONF, SNMP — and get back structured data over a clean HTTP interface. Async job queuing, response caching, service orchestration, and horizontal scaling are all built in.

## Architecture

```mermaid
graph TB
    Client["Client
    POST /getconfig
    POST /setconfig
    POST /script
    POST /service
    GET /task/{id}"]

    subgraph netpalm["netpalm cluster"]
        API["FastAPI :9000"]
        DB[(PostgreSQL)]
        Scheduler["Scheduler
        (outbox relay)"]
        Kafka["Kafka (KRaft)"]
        E1["Executor"]
        E2["Executor"]
        E3["Executor ..."]
    end

    Devices[/"Network Devices
    SSH · Telnet · NETCONF · RESTCONF · SNMP"/]

    Client -->|HTTP| API
    API --> DB
    Scheduler --> DB
    Scheduler --> Kafka
    Kafka --> E1 & E2 & E3
    E1 & E2 & E3 --> Devices
    E1 & E2 & E3 -->|result| DB
```

### How a request flows

```mermaid
sequenceDiagram
    participant C as Client
    participant A as API Server
    participant DB as PostgreSQL
    participant S as Scheduler
    participant K as Kafka
    participant E as Executor
    participant D as Device

    C->>A: POST /getconfig
    A->>DB: Insert job (pending)
    A-->>C: 202 {task_id}
    S->>DB: Poll pending jobs
    S->>K: Publish to topic
    K->>E: Consume job
    E->>D: Connect & run command
    D-->>E: Response
    E->>DB: Write result (finished)
    C->>A: GET /task/{task_id}
    A->>DB: Read result
    A-->>C: 200 {task_result}
```

## Drivers

| Driver | Protocol | Use case |
|--------|----------|----------|
| [Netmiko](https://github.com/ktbyers/netmiko) | SSH / Telnet | CLI commands on 50+ device types |
| [NAPALM](https://github.com/napalm-automation/napalm) | SSH | Vendor-abstracted getters and config management |
| [ncclient](https://github.com/ncclient/ncclient) | NETCONF | YANG model-driven config and state |
| [PureSNMP](https://github.com/exhuma/puresnmp) | SNMP | GET / SET / WALK operations |
| [Requests](https://github.com/psf/requests) | RESTCONF | HTTP-based YANG operations |

All drivers share a common interface: `connect()`, `sendcommand()`, `config()`, `logout()`. New drivers are auto-discovered at startup.

## Quick Start

```bash
git clone https://github.com/tbotnz/netpalm.git
cd netpalm
docker compose up -d --build
```

API is live at `http://localhost:9000` with a Swagger UI. Default API key is in `config/.env.example`.

### Example: get config from a device

```bash
curl -s -X POST http://localhost:9000/getconfig/netmiko \
  -H "Content-Type: application/json" \
  -H "x-api-key: 2a84465a-cf38-46b2-9d86-b84Q7d57f288" \
  -d '{
    "connection_args": {
      "device_type": "cisco_ios",
      "host": "10.0.2.33",
      "username": "admin",
      "password": "admin"
    },
    "command": "show ip int brief",
    "queue_strategy": "fifo"
  }'
```

Response:
```json
{
  "status": "success",
  "data": {
    "task_id": "b380cf2b-ba78-4c24-8b24-xxxxxxxxxxxx",
    "task_status": "queued"
  }
}
```

Then poll the result:
```bash
curl -s http://localhost:9000/task/b380cf2b-ba78-4c24-8b24-xxxxxxxxxxxx \
  -H "x-api-key: 2a84465a-cf38-46b2-9d86-b84Q7d57f288"
```

## API Endpoints

| Method | Path | What it does |
|--------|------|--------------|
| `POST` | `/getconfig/{driver}` | Read device state (CLI, NETCONF, SNMP, RESTCONF) |
| `POST` | `/setconfig/{driver}` | Deploy configuration with optional pre/post checks |
| `POST` | `/setconfig/dry-run` | Test a config change without committing |
| `GET/POST` | `/script` | List or execute custom Python scripts |
| `POST` | `/service/instance/create/{model}` | Create a multi-device service instance |
| `PATCH` | `/service/instance/update/{id}` | Update a service instance |
| `POST` | `/service/instance/delete/{id}` | Delete a service instance |
| `GET` | `/task/{task_id}` | Poll async task result |
| `GET/POST/DELETE` | `/template` | Manage TextFSM / TTP / Jinja2 templates |
| `GET/POST/PATCH/DELETE` | `/schedule/` | Manage scheduled jobs |

Full OpenAPI docs are served at `/` when the container is running.

## Features

### Queueing strategies

- **FIFO** — pooled workers, first-in-first-out. Good default for read operations.
- **Pinned** — one queue per device. Serializes all tasks for that host, prevents connection stomping.

```mermaid
graph LR
    subgraph Kafka Topics
        FIFO["netpalm.jobs.fifo"]
        P1["netpalm.jobs.pinned.10.0.1.1"]
        P2["netpalm.jobs.pinned.10.0.1.2"]
    end

    Pool["Worker Pool
    (any executor)"]
    EA["Executor A"]
    EB["Executor B"]

    FIFO --> Pool
    P1 --> EA
    P2 --> EB
```

### Caching

Responses can be cached per-request. Config changes automatically poison the cache for that device.

```json
{
  "cache": {
    "enabled": true,
    "ttl": 30,
    "poison": false
  }
}
```

Global toggle: `NETPALM_REDIS_CACHE_DEFAULT_TIMEOUT` in your `.env`.

### Pre/Post Checks

Validate device state before and after deploying config:

```json
{
  "pre_checks": [{
    "match_type": "include",
    "match_str": ["hostname router1"],
    "get_config_args": { "command": "show run | i hostname" }
  }]
}
```

If a pre-check fails, the config is not deployed. If a post-check fails, the task errors out.

### Service Templates

Model-driven, multi-device orchestration with lifecycle management. Services support create, retrieve, delete, validate, and health check operations with automatic versioning and rollback.

```mermaid
stateDiagram-v2
    [*] --> deploying
    deploying --> deployed
    deployed --> updating
    updating --> deployed
    updating --> errored : auto-rollback
    deployed --> deleting
    deleting --> deleted
    deleted --> [*]
```

Drop your service definitions in `netpalm/backend/plugins/extensibles/services/`.

### Extensibility

Bring your own:

| What | Where |
|------|-------|
| Jinja2 config templates | `netpalm/backend/plugins/extensibles/j2_config_templates/` |
| Jinja2 webhook templates | `netpalm/backend/plugins/extensibles/j2_webhook_templates/` |
| TTP parsing templates | `netpalm/backend/plugins/extensibles/ttp_templates/` |
| Custom Python scripts | `netpalm/backend/plugins/extensibles/custom_scripts/` |
| Custom webhooks | `netpalm/backend/plugins/extensibles/custom_webhooks/` |
| Service models | `netpalm/backend/plugins/extensibles/services/` |

Scripts get auto-documented in the Swagger UI. Jinja2 templates get auto-generated JSON schemas.

### Parsing

- **TextFSM** — structured CLI output via [NTC Templates](https://github.com/networktocode/ntc-templates) (included)
- **TTP** — Jinja2-like template parsing
- **Genie** — Cisco Genie parsers via Netmiko
- **NAPALM getters** — vendor-abstracted structured data
- **XML to JSON** — automatic NETCONF response rendering

### Events & Webhooks

netpalm has a Kafka-native event system. External events (syslog, SNMP traps) flow in, job results flow out, and webhooks fire on task completion.

```mermaid
graph LR
    subgraph "Inbound Events"
        Syslog["Syslog Source"]
        SNMP["SNMP Trap Source"]
    end

    subgraph Kafka
        ST["netpalm.events.syslog"]
        SNT["netpalm.events.snmp-trap"]
        JF["netpalm.jobs.fifo"]
        JP["netpalm.jobs.pinned.*"]
        RT["netpalm.results"]
    end

    subgraph netpalm
        EL["Event Listeners
        (user-defined)"]
        Executor
        Manager["NetpalmManager"]
    end

    subgraph "Outbound"
        WH["Webhooks
        (REST, Elastic,
        ServiceNow, ...)"]
    end

    Syslog --> ST
    SNMP --> SNT
    ST & SNT --> EL
    EL -->|"triggers actions via"| Manager
    Manager -->|"enqueues jobs"| JF & JP
    JF & JP --> Executor
    Executor --> RT
    Executor -->|"on completion"| WH
```

**Inbound** — External systems publish to Kafka event topics. User-defined `EventListener` plugins subscribe to topics, parse messages, and react by calling the manager (e.g. auto-remediate a syslog alert by pushing config).

**Outbound** — When any operation completes, an optional webhook fires. Built-in webhooks include REST POST, Elasticsearch indexing, and ServiceNow patching. Add your own in `netpalm/backend/plugins/extensibles/custom_webhooks/`.

**Kafka topics:**

| Topic | Direction | Purpose |
|-------|-----------|---------|
| `netpalm.jobs.fifo` | Internal | FIFO job queue |
| `netpalm.jobs.pinned.{host}` | Internal | Per-device pinned queue |
| `netpalm.results` | Internal | Task execution results |
| `netpalm.events.syslog` | Inbound | Syslog events from external sources |
| `netpalm.events.snmp-trap` | Inbound | SNMP trap events from external sources |

Event listeners are auto-discovered from `netpalm/backend/plugins/event_listeners/`.

## Scaling

Every component scales independently. Executors are stateless Kafka consumers — add more to increase throughput.

```bash
# scale executors to 5
docker compose up -d --scale netpalm-executor=5
```

```mermaid
graph TB
    A1["API Server"] & A2["API Server"] & A3["API Server"]
    DB["PostgreSQL + Kafka"]
    E1["Executor"] & E2["Executor"] & E3["Executor"] & E4["Executor"] & E5["Executor"]

    A1 & A2 & A3 --> DB
    DB --> E1 & E2 & E3 & E4 & E5
```

For production, deploy on Kubernetes or Docker Swarm.

## Configuration

All config is via environment variables. Copy `config/.env.example` to `config/.env` and edit:

```bash
# Core
NETPALM_API_KEY=2a84465a-cf38-46b2-9d86-b84Q7d57f288
NETPALM_LISTEN_PORT=9000

# PostgreSQL
NETPALM_DATABASE_URL=postgresql+asyncpg://netpalm:netpalm@postgres:5432/netpalm

# Kafka
NETPALM_KAFKA_BOOTSTRAP_SERVERS=kafka:9092

# Redis (caching only)
NETPALM_REDIS_SERVER=redis
NETPALM_REDIS_CACHE_DEFAULT_TIMEOUT=300

# Workers
NETPALM_FIFO_PROCESS_PER_NODE=10
```

See `config/.env.example` for all available options including TLS, webhook defaults, and logging.

## Stack

| Component | Technology |
|-----------|------------|
| API | FastAPI + Uvicorn |
| Database | PostgreSQL 16 |
| Message bus | Apache Kafka 3.7 (KRaft, no Zookeeper) |
| Cache | Redis 7 |
| Task relay | Transactional outbox pattern |
| Models | Pydantic v2 |
| ORM | SQLAlchemy (async) |
| Runtime | Python 3.12 |

## Contributing

Read [`CONTRIBUTING.md`](https://github.com/tbotnz/netpalm/blob/master/CONTRIBUTING.md) before opening a PR.

Find us in `#netpalm` on the [Network to Code Slack](https://networktocode.slack.com).
