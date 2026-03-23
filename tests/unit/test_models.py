"""Tests for Pydantic models and DB models."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from netpalm.backend.core.models.models import (
    CacheConfig,
    GetConfig,
    LibraryName,
    NetpalmEvent,
    QueueStrategy,
    ResultMessage,
    ScheduleBase,
    ScheduleInterval,
    Script,
    ServiceInstanceData,
    ServiceVersionSummary,
    SetConfig,
    TaskMessage,
    TaskResponse,
    TFSMPushTemplateModel,
    TFSMTemplateAdd,
    TFSMTemplateMatch,
    TFSMTemplateRemove,
    UniversalTemplateAdd,
    UniversalTemplateRemove,
    Webhook,
)


class TestQueueStrategy:
    def test_fifo(self):
        assert QueueStrategy.fifo == "fifo"

    def test_pinned(self):
        assert QueueStrategy.pinned == "pinned"


class TestLibraryName:
    def test_all_libraries(self):
        expected = {"napalm", "ncclient", "restconf", "netmiko", "puresnmp"}
        assert {l.value for l in LibraryName} == expected


class TestTaskMessage:
    def test_create(self):
        tid = uuid.uuid4()
        msg = TaskMessage(
            task_id=tid,
            method="getconfig",
            kwargs={"host": "10.0.0.1"},
        )
        assert msg.task_id == tid
        assert msg.method == "getconfig"
        assert msg.queue_strategy == QueueStrategy.fifo
        assert msg.pinned_host is None

    def test_pinned(self):
        msg = TaskMessage(
            task_id=uuid.uuid4(),
            method="setconfig",
            kwargs={},
            queue_strategy=QueueStrategy.pinned,
            pinned_host="router1",
        )
        assert msg.queue_strategy == QueueStrategy.pinned
        assert msg.pinned_host == "router1"

    def test_roundtrip_json(self):
        msg = TaskMessage(
            task_id=uuid.uuid4(),
            method="getconfig",
            kwargs={"command": "show version"},
        )
        json_str = msg.model_dump_json()
        restored = TaskMessage.model_validate_json(json_str)
        assert restored.task_id == msg.task_id
        assert restored.kwargs == msg.kwargs


class TestResultMessage:
    def test_success(self):
        msg = ResultMessage(
            task_id=uuid.uuid4(),
            status="finished",
            result={"output": "data"},
        )
        assert msg.error is None

    def test_failure(self):
        msg = ResultMessage(
            task_id=uuid.uuid4(),
            status="failed",
            error="connection timeout",
        )
        assert msg.result is None


class TestNetpalmEvent:
    def test_create(self):
        event = NetpalmEvent(
            source_topic="netpalm.events.syslog",
            device_host="10.0.0.1",
            event_type="syslog",
            raw=b"raw data",
            data={"message": "link down"},
        )
        assert event.source_topic == "netpalm.events.syslog"
        assert event.raw == b"raw data"

    def test_optional_host(self):
        event = NetpalmEvent(
            source_topic="topic",
            event_type="test",
            raw=b"",
        )
        assert event.device_host is None
        assert event.data == {}


class TestTaskResponse:
    def test_basic(self):
        resp = TaskResponse(
            task_id=uuid.uuid4(),
            status="pending",
        )
        assert resp.result is None


class TestServiceModels:
    def test_service_instance_data(self):
        now = datetime.now(timezone.utc)
        data = ServiceInstanceData(
            service_id=uuid.uuid4(),
            service_model="vlan_service",
            state="deployed",
            data={"vlan_id": 100},
            created_at=now,
            updated_at=now,
            current_version=3,
        )
        assert data.current_version == 3

    def test_service_version_summary(self):
        now = datetime.now(timezone.utc)
        summary = ServiceVersionSummary(
            version_id=uuid.uuid4(),
            service_id=uuid.uuid4(),
            version=1,
            state="deployed",
            created_at=now,
        )
        assert summary.version == 1


class TestConfigModels:
    def test_get_config(self):
        cfg = GetConfig(
            library="netmiko",
            connection_args={"host": "10.0.0.1", "device_type": "cisco_ios"},
            command="show version",
        )
        assert cfg.library == LibraryName.netmiko

    def test_set_config(self):
        cfg = SetConfig(
            library="napalm",
            connection_args={"hostname": "10.0.0.1"},
        )
        assert cfg.library == LibraryName.napalm
        assert cfg.j2config is None

    def test_cache_config_defaults(self):
        cc = CacheConfig()
        assert cc.enabled is False
        assert cc.poison is False

    def test_script(self):
        s = Script(script="hello_world", args={"hello": "world"})
        assert s.script == "hello_world"

    def test_webhook(self):
        w = Webhook(name="my_hook", args={"key": "val"})
        assert w.name == "my_hook"


class TestTemplateModels:
    def test_tfsm_push(self):
        m = TFSMPushTemplateModel(
            driver="cisco_ios", command="show version", template_text="Value UPTIME (.*)"
        )
        assert m.driver == "cisco_ios"

    def test_tfsm_add(self):
        m = TFSMTemplateAdd(key="abc", driver="cisco_ios", command="show version")
        assert m.key == "abc"

    def test_tfsm_remove(self):
        m = TFSMTemplateRemove(template="old_template")
        assert m.template == "old_template"

    def test_tfsm_match(self):
        m = TFSMTemplateMatch(driver="cisco_ios", command="show version")
        assert m.command == "show version"

    def test_universal_add(self):
        m = UniversalTemplateAdd(base64_payload="dGVzdA==", name="test")
        assert m.name == "test"

    def test_universal_remove(self):
        m = UniversalTemplateRemove(name="test")
        assert m.name == "test"


class TestScheduleModels:
    def test_schedule_interval(self):
        s = ScheduleInterval(
            hours=1,
            minutes=30,
            schedule_payload=ScheduleBase(path="/getconfig", payload={"host": "10.0.0.1"}),
        )
        assert s.hours == 1
        assert s.schedule_payload.path == "/getconfig"
