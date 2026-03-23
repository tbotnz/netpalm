from typing import Any

from pydantic import BaseModel, ConfigDict

from netpalm.backend.core.models.models import (
    CacheConfig,
    GenericPrePostCheck,
    J2Config,
    QueueStrategy,
    Webhook,
)


class NetmikoSendConfigArgs(BaseModel):
    command_string: str | None = None
    expect_string: str | None = None
    delay_factor: int | None = None
    commit_label: str | None = None
    max_loops: int | None = None
    auto_find_prompt: bool | None = None
    strip_prompt: bool | None = None
    strip_command: bool | None = None
    normalize: bool | None = None
    use_textfsm: bool | None = None
    textfsm_template: str | None = None
    use_ttp: bool | None = None
    ttp_template: str | None = None
    use_genie: bool | None = None
    cmd_verify: bool | None = None


class NetmikoConnectionArgs(BaseModel):
    ip: str | None = None
    host: str | None = None
    username: str
    password: str
    secret: str | None = None
    port: int = 22
    device_type: str
    verbose: bool | None = None
    global_delay_factor: int | None = 1
    global_cmd_verify: bool | None = None
    use_keys: bool | None = None
    key_file: str | None = None
    pkey: str | None = None
    passphrase: str | None = None
    allow_agent: bool = False
    ssh_strict: bool | None = None
    system_host_keys: bool = False
    alt_host_keys: bool = False
    alt_key_file: str = ""
    ssh_config_file: str | None = None
    timeout: int = 100
    session_timeout: int | None = None
    auth_timeout: float | None = None
    blocking_timeout: int = 20
    banner_timeout: int = 15
    keepalive: int = 0
    default_enter: str | None = None
    response_return: str | None = None
    serial_settings: str | None = None
    fast_cli: bool = False
    session_log: str | None = None
    session_log_record_writes: bool = False
    session_log_file_mode: str = "write"
    allow_auto_change: bool = False
    encoding: str = "ascii"
    sock: bool | None = None
    auto_connect: bool = True


class NetmikoGetConfig(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "library": "netmiko",
                "connection_args": {
                    "device_type": "cisco_ios",
                    "host": "10.0.2.33",
                    "username": "admin",
                    "password": "admin",
                },
                "command": "show ip int brief",
                "args": {"use_textfsm": True},
                "queue_strategy": "fifo",
                "cache": {"enabled": True, "ttl": 300, "poison": False},
            }
        }
    )

    connection_args: NetmikoConnectionArgs
    command: Any
    args: NetmikoSendConfigArgs | None = None
    webhook: Webhook | None = None
    queue_strategy: QueueStrategy | None = None
    post_checks: list[GenericPrePostCheck] | None = None
    cache: CacheConfig | None = None
    enable_mode: bool = False


class NetmikoSetConfig(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "library": "netmiko",
                "connection_args": {
                    "device_type": "cisco_ios",
                    "host": "10.0.2.33",
                    "username": "admin",
                    "password": "admin",
                },
                "config": ["hostname cat"],
                "queue_strategy": "fifo",
            }
        }
    )

    connection_args: dict[str, Any]
    config: Any | None = None
    args: NetmikoSendConfigArgs | None = None
    j2config: J2Config | None = None
    webhook: Webhook | None = None
    queue_strategy: QueueStrategy | None = None
    pre_checks: list[GenericPrePostCheck] | None = None
    post_checks: list[GenericPrePostCheck] | None = None
    enable_mode: bool = False
