from typing import Optional, Any, List

from pydantic import BaseModel

from netpalm.backend.core.models.models import GenericPrePostCheck
from netpalm.backend.core.models.models import J2Config, CacheConfig
from netpalm.backend.core.models.models import QueueStrategy
from netpalm.backend.core.models.models import Webhook


class NetmikoSendConfigArgs(BaseModel):
    command_string: Optional[str] = None
    expect_string: Optional[str] = None
    delay_factor: Optional[int] = None
    commit_label: Optional[str] = None
    max_loops: Optional[int] = None
    auto_find_prompt: Optional[bool] = None
    strip_prompt: Optional[bool] = None
    strip_command: Optional[bool] = None
    normalize: Optional[bool] = None
    use_textfsm: Optional[bool] = None
    textfsm_template: Optional[str] = None
    use_ttp: Optional[bool] = None
    ttp_template: Optional[str] = None
    use_genie: Optional[bool] = None
    cmd_verify: Optional[bool] = None


class NetmikoConnectionArgs(BaseModel):
    ip: Optional[str] = None
    host: Optional[str] = None
    username: str
    password: str
    secret: Optional[str] = None
    port: Optional[int] = 22
    device_type: str
    verbose: Optional[bool] = None
    global_delay_factor: Optional[int] = 1
    global_cmd_verify: Optional[bool] = None
    use_keys: Optional[bool] = None
    key_file: Optional[str] = None
    pkey: Optional[str] = None
    passphrase: Optional[str] = None
    allow_agent: Optional[bool] = False
    ssh_strict: Optional[bool] = None
    system_host_keys: Optional[bool] = False
    alt_host_keys: Optional[bool] = False
    alt_key_file: Optional[str] = ""
    ssh_config_file: Optional[str] = None
    timeout: Optional[int] = 100
    session_timeout: Optional[int] = None
    auth_timeout: Optional[float] = None
    blocking_timeout: Optional[int] = 20
    banner_timeout: Optional[int] = 15
    keepalive: Optional[int] = 0
    default_enter: Optional[str] = None
    response_return: Optional[str] = None
    serial_settings: Optional[str] = None
    fast_cli: Optional[bool] = False
    session_log: Optional[str] = None
    session_log_record_writes: Optional[bool] = False
    session_log_file_mode: Optional[str] = "write"
    allow_auto_change: Optional[bool] = False
    encoding: Optional[str] = "ascii"
    sock: Optional[bool] = None
    auto_connect: Optional[bool] = True


class NetmikoGetConfig(BaseModel):
    connection_args: NetmikoConnectionArgs
    command: Any
    args: Optional[NetmikoSendConfigArgs] = None
    webhook: Optional[Webhook] = None
    queue_strategy: Optional[QueueStrategy] = None
    post_checks: Optional[List[GenericPrePostCheck]] = None
    cache: Optional[CacheConfig] = {}
    ttl: Optional[int] = None
    enable_mode: Optional[bool] = False

    class Config:
        json_schema_extra = {
            "example": {
                "library": "netmiko",
                "connection_args": {
                    "device_type": "cisco_ios",
                    "host": "10.0.2.33",
                    "username": "admin",
                    "password": "admin"
                },
                "command": "show ip int brief",
                "args": {
                    "use_textfsm": True
                },
                "queue_strategy": "fifo",
                "cache": {
                    "enabled": True,
                    "ttl": 300,
                    "poison": False
                }
            }
        }


class NetmikoSetConfig(BaseModel):
    connection_args: dict
    config: Optional[Any] = None
    args: Optional[NetmikoSendConfigArgs] = {}
    j2config: Optional[J2Config] = None
    webhook: Optional[Webhook] = None
    queue_strategy: Optional[QueueStrategy] = None
    pre_checks: Optional[List[GenericPrePostCheck]] = None
    post_checks: Optional[List[GenericPrePostCheck]] = None
    enable_mode: Optional[bool] = False
    ttl: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "library": "netmiko",
                "connection_args": {
                    "device_type": "cisco_ios",
                    "host": "10.0.2.33",
                    "username": "admin",
                    "password": "admin"
                },
                "config": ["hostname cat"],
                "queue_strategy": "pinned"
            }
        }
