from typing import Optional

from pydantic import BaseModel

from backend.core.models.base_models import BaseConnectionArgs, BaseGetConfig, BaseSetConfig


class NetmikoSendConfigArgs(BaseModel):
    command_string: Optional[str] = None
    expect_string: Optional[str] = None
    delay_factor: Optional[int] = None
    max_loops: Optional[int] = None
    auto_find_prompt: Optional[bool] = None
    strip_prompt: Optional[bool] = None
    strip_command: Optional[bool] = None
    normalize: Optional[bool] = None
    use_textfsm: Optional[bool] = None
    textfsm_template: Optional[str] = None
    use_genie: Optional[bool] = None
    cmd_verify: Optional[bool] = None


class NetmikoConnectionArgs(BaseConnectionArgs):
    ip: Optional[str] = None
    secret: Optional[str] = None
    device_type: str
    verbose: Optional[bool] = None
    global_delay_factor: Optional[int] = None
    global_cmd_verify: Optional[bool] = None
    use_keys: Optional[bool] = None
    key_file: Optional[str] = None
    pkey: Optional[str] = None
    passphrase: Optional[str] = None
    allow_agent: Optional[bool] = None
    ssh_strict: Optional[bool] = None
    system_host_keys: Optional[bool] = None
    alt_host_keys: Optional[bool] = None
    alt_key_file: Optional[str] = None
    ssh_config_file: Optional[str] = None
    timeout: Optional[int] = None
    session_timeout: Optional[int] = None
    auth_timeout: Optional[float] = None
    blocking_timeout: Optional[int] = None
    banner_timeout: Optional[int] = None
    keepalive: Optional[int] = None
    default_enter: Optional[str] = None
    response_return: Optional[str] = None
    serial_settings: Optional[str] = None
    fast_cli: Optional[bool] = None
    session_log: Optional[str] = None
    session_log_record_writes = False
    session_log_file_mode: Optional[str] = None
    allow_auto_change: Optional[bool] = None
    encoding: Optional[str] = None
    sock: Optional[bool] = None
    auto_connect: Optional[bool] = None


class NetmikoGetConfig(BaseGetConfig):
    args: Optional[NetmikoSendConfigArgs] = None

    class Config:
        schema_extra = {
            "example": {
                "library": "netmiko",
                "connection_args": {
                    "device_type": "cisco_ios", "host": "10.0.2.33", "username": "admin", "password": "admin"
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


class NetmikoSetConfig(BaseSetConfig):
    args: Optional[NetmikoSendConfigArgs] = {}

    class Config:
        schema_extra = {
            "example": {
                "library": "netmiko",
                "connection_args": {
                    "device_type": "cisco_ios", "host": "10.0.2.33", "username": "admin", "password": "admin"
                },
                "config": ["hostname cat"],
                "queue_strategy": "pinned"
            }
        }
