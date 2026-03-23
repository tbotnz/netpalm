<p align="center">
  <img src="/static/images/netpalm.png" width="280" />
  <br/><br/>
  <strong>REST API broker for network devices</strong>
  <br/><br/>
  <a href="https://github.com/tbotnz/netpalm/actions"><img src="https://github.com/tbotnz/netpalm/workflows/tests/badge.svg" /></a>
  <img src="https://img.shields.io/github/stars/tbotnz/netpalm" />
  <img src="https://img.shields.io/github/license/tbotnz/netpalm" />
  <a href="https://networktocode.slack.com"><img src="https://img.shields.io/badge/slack-%23netpalm-orange" /></a>
</p>

---

One API to talk to every network device you own. SSH, Telnet, NETCONF, RESTCONF, SNMP — netpalm normalises them all behind a single async REST interface with job queuing, caching, service orchestration, event-driven automation, and horizontal scaling built in.

## Quick Start

```bash
git clone https://github.com/tbotnz/netpalm.git && cd netpalm
docker compose up -d --build
# Swagger UI → http://localhost:9000
```

```bash
# grab config from a device
curl -sX POST http://localhost:9000/getconfig/netmiko \
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
# → { "data": { "task_id": "b380cf2b-..." } }

# poll for the result
curl -s http://localhost:9000/task/b380cf2b-... \
  -H "x-api-key: 2a84465a-cf38-46b2-9d86-b84Q7d57f288"
```

---

## How It Works

```mermaid
graph TB
    Client(("Client"))

    subgraph netpalm
        API["FastAPI
        :9000"]
        DB[(PostgreSQL)]
        Sched["Scheduler"]
        K["Kafka
        (KRaft)"]
        E1["Executor"] & E2["Executor"] & E3["Executor"]
        Cache["Redis
        (cache)"]
    end

    Devices[/"Network Devices
    SSH · Telnet · NETCONF · RESTCONF · SNMP"/]

    Client -->|"HTTP"| API
    API -->|"write job"| DB
    API -.->|"check cache"| Cache
    Sched -->|"poll pending"| DB
    Sched -->|"publish"| K
    K --> E1 & E2 & E3
    E1 & E2 & E3 -->|"connect"| Devices
    E1 & E2 & E3 -->|"write result"| DB
```

Every request is async. You POST, get a `task_id` back immediately, and poll for the result. Nothing blocks.

```mermaid
sequenceDiagram
    participant C as Client
    participant A as API
    participant DB as PostgreSQL
    participant S as Scheduler
    participant K as Kafka
    participant E as Executor
    participant D as Device

    C->>A: POST /getconfig
    A->>DB: Insert job (pending)
    A-->>C: 202 — task_id

    S->>DB: Poll pending
    S->>K: Publish job

    K->>E: Deliver job
    E->>D: Connect + command
    D-->>E: Output
    E->>DB: Write result (finished)

    C->>A: GET /task/{id}
    A->>DB: Read result
    A-->>C: 200 — result
```

---

## Drivers

| Driver | Protocol | Use case |
|--------|----------|----------|
| [Netmiko](https://github.com/ktbyers/netmiko) | SSH / Telnet | CLI commands across 50+ platforms |
| [NAPALM](https://github.com/napalm-automation/napalm) | SSH | Vendor-abstracted getters and config management |
| [ncclient](https://github.com/ncclient/ncclient) | NETCONF | YANG model-driven config and state |
| [PureSNMP](https://github.com/exhuma/puresnmp) | SNMP | GET / SET / WALK |
| [Requests](https://github.com/psf/requests) | RESTCONF | HTTP-based YANG operations |

All drivers implement a common interface — `connect()`, `sendcommand()`, `config()`, `logout()` — and are auto-discovered at startup. Adding a new driver is one file.

---

## API

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/getconfig/{driver}` | Read device state |
| `POST` | `/setconfig/{driver}` | Push config (with optional pre/post checks) |
| `POST` | `/setconfig/dry-run` | Validate without committing |
| `GET/POST` | `/script` | List or run custom Python scripts |
| `POST` | `/service/instance/create/{model}` | Create multi-device service |
| `PATCH` | `/service/instance/update/{id}` | Update service |
| `POST` | `/service/instance/delete/{id}` | Tear down service |
| `GET` | `/task/{task_id}` | Poll async result |
| `GET/POST/DELETE` | `/template` | Manage TextFSM / TTP / Jinja2 templates |
| `GET/POST/PATCH/DELETE` | `/schedule/` | Scheduled jobs |

Every running instance serves full OpenAPI docs at `/`.

---

## Queueing

Two strategies, chosen per-request:

```mermaid
graph LR
    subgraph "Kafka Topics"
        FIFO["netpalm.jobs.fifo"]
        P1["netpalm.jobs.pinned.10.0.1.1"]
        P2["netpalm.jobs.pinned.10.0.1.2"]
    end

    Pool["Worker Pool"]
    EA["Executor A"]
    EB["Executor B"]

    FIFO -->|"round-robin"| Pool
    P1 -->|"dedicated"| EA
    P2 -->|"dedicated"| EB
```

- **FIFO** — jobs go to a shared pool. Fast, no ordering guarantees per device.
- **Pinned** — one queue per host. Serialises all work for that device, prevents connection stomping during config pushes.

---

## Events & Webhooks

```mermaid
graph LR
    subgraph "External Sources"
        SL(["Syslog"])
        TR(["SNMP Traps"])
    end

    subgraph "Kafka"
        ET1["netpalm.events.syslog"]
        ET2["netpalm.events.snmp-trap"]
        JT["Job Topics"]
        RT["netpalm.results"]
    end

    subgraph "netpalm"
        EL["Event Listeners"]
        MGR["Manager"]
        EX["Executors"]
    end

    subgraph "Integrations"
        WH["Webhooks"]
        ES(["Elasticsearch"])
        SN(["ServiceNow"])
        REST(["REST endpoint"])
    end

    SL --> ET1
    TR --> ET2
    ET1 & ET2 --> EL
    EL -->|"react"| MGR
    MGR --> JT
    JT --> EX
    EX --> RT
    EX -->|"on complete"| WH
    WH --> ES & SN & REST
```

**Inbound** — External systems push syslog or SNMP trap messages onto Kafka event topics. Your `EventListener` plugins consume them and react through the manager — auto-remediate, log, alert, whatever you need.

**Outbound** — Every completed task can fire a webhook. Ship results to Elasticsearch, patch a ServiceNow ticket, or POST to any REST endpoint. Drop a script in `custom_webhooks/` and it just works.

| Topic | Direction | Purpose |
|-------|-----------|---------|
| `netpalm.jobs.fifo` | Internal | FIFO job queue |
| `netpalm.jobs.pinned.{host}` | Internal | Per-device pinned queue |
| `netpalm.results` | Internal | Completed task results |
| `netpalm.events.syslog` | Inbound | Syslog from external sources |
| `netpalm.events.snmp-trap` | Inbound | SNMP traps from external sources |

---

## Services

Model-driven, multi-device orchestration with versioning and automatic rollback.

```mermaid
stateDiagram-v2
    [*] --> deploying
    deploying --> deployed
    deployed --> updating
    updating --> deployed
    updating --> errored : auto‑rollback
    deployed --> deleting
    deleting --> deleted
    deleted --> [*]
```

Define a service model + implementation, drop it in `services/`, and netpalm gives you a full lifecycle API with state tracking, version snapshots, and rollback — no extra code required.

---

## Caching & Checks

**Caching** — per-request, backed by Redis. Config changes auto-poison the cache for that device.

```json
{ "cache": { "enabled": true, "ttl": 30, "poison": false } }
```

**Pre/Post Checks** — validate device state before and after config deployment. If a check fails, the change doesn't go through.

```json
{
  "pre_checks": [{
    "match_type": "include",
    "match_str": ["hostname router1"],
    "get_config_args": { "command": "show run | i hostname" }
  }]
}
```

---

## Parsing

| Engine | What it does |
|--------|-------------|
| [NTC Templates](https://github.com/networktocode/ntc-templates) (TextFSM) | Structured CLI output — included out of the box |
| TTP | Jinja2-style template parsing for semi-structured text |
| Genie | Cisco Genie parsers via Netmiko |
| NAPALM getters | Vendor-abstracted structured data |
| XML → JSON | Automatic NETCONF response rendering |

---

## Extensibility

Everything is a plugin. Drop files in the right directory and they're auto-discovered.

| Plugin type | Directory |
|------------|-----------|
| Jinja2 config templates | `extensibles/j2_config_templates/` |
| Jinja2 webhook templates | `extensibles/j2_webhook_templates/` |
| TTP parsing templates | `extensibles/ttp_templates/` |
| Python scripts | `extensibles/custom_scripts/` |
| Webhook handlers | `extensibles/custom_webhooks/` |
| Service definitions | `extensibles/services/` |
| Event listeners | `event_listeners/` |

Scripts and service models auto-generate OpenAPI docs. Jinja2 templates auto-generate JSON schemas.

---

## Scaling

Every component is stateless (except the data stores) and scales independently.

```mermaid
graph TB
    LB(["Load Balancer"])
    A1["API"] & A2["API"] & A3["API"]
    DB[("PostgreSQL")] & K["Kafka"]
    E1["Executor"] & E2["Executor"] & E3["Executor"] & E4["Executor"] & E5["Executor"]

    LB --> A1 & A2 & A3
    A1 & A2 & A3 --> DB
    DB --> K
    K --> E1 & E2 & E3 & E4 & E5
```

```bash
docker compose up -d --scale netpalm-executor=5 --scale netpalm-api-server=3
```

For production, run on Kubernetes or Docker Swarm.

---

## Configuration

Environment variables via `config/.env`. Copy from the example and edit:

```bash
cp config/.env.example config/.env
```

```bash
# Core
NETPALM_API_KEY=2a84465a-cf38-46b2-9d86-b84Q7d57f288
NETPALM_LISTEN_PORT=9000

# Data stores
NETPALM_DATABASE_URL=postgresql+asyncpg://netpalm:netpalm@postgres:5432/netpalm
NETPALM_KAFKA_BOOTSTRAP_SERVERS=kafka:9092
NETPALM_REDIS_SERVER=redis

# Tuning
NETPALM_FIFO_PROCESS_PER_NODE=10
NETPALM_REDIS_CACHE_DEFAULT_TIMEOUT=300
```

See [`config/.env.example`](config/.env.example) for all options — TLS, webhooks, logging, and more.

---

## Stack

| | |
|---|---|
| **API** | FastAPI + Uvicorn |
| **Database** | PostgreSQL 16 |
| **Message bus** | Apache Kafka 3.7 (KRaft — no Zookeeper) |
| **Cache** | Redis 7 |
| **Patterns** | Transactional outbox, async task queue |
| **Models** | Pydantic v2 |
| **ORM** | SQLAlchemy (async) |
| **Runtime** | Python 3.12 |

---

## Contributing

Read [`CONTRIBUTING.md`](CONTRIBUTING.md) first. Find us in `#netpalm` on the [Network to Code Slack](https://networktocode.slack.com).
