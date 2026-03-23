import json
import logging
import logging.config
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict

from netpalm.backend.core.security.whitelist import DeviceWhitelist

try:
    yaml_loader = yaml.CSafeLoader
except AttributeError:
    yaml_loader = yaml.SafeLoader

log = logging.getLogger(__name__)
CONFIG_FILENAME = "config/config.json"
DEFAULTS_FILENAME = "config/defaults.json"


class ScrubFilter(logging.Filter):
    """Logging filter that scrubs sensitive fields like passwords and keys."""

    import re

    PATTERNS = [
        re.compile(r"(?:[aA][sS][sS][wW][oO][rR][dD](?:'|\"): (?:'|\")(.*?)(?:'|\"))"),
        re.compile(r"(?:[oO][kK][eE][nN](?:'|\"): (?:'|\")(.*?)(?:'|\"))"),
        re.compile(r"(?:[kK][eE][yY](?:'|\"): (?:'|\")(.*?)(?:'|\"))"),
        re.compile(r"(?:[eE][cC][rR][eE][tT](?:'|\"): (?:'|\")(.*?)(?:'|\"))"),
        re.compile(r"(?:[oO][mM][uU][nN][iI][tT][yY](?:'|\"): (?:'|\")(.*?)(?:'|\"))"),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = self._scrub(record.msg)
        if isinstance(record.args, dict):
            for k in record.args:
                record.args[k] = self._scrub(record.args[k])
        elif record.args:
            record.args = tuple(self._scrub(arg) for arg in record.args)
        return True

    def _scrub(self, message: Any) -> Any:
        if not isinstance(message, str):
            return message
        result = message
        for pattern in self.PATTERNS:
            m = pattern.search(result)
            if m:
                result = result.replace(m.group(1), "******")
        return result


def _load_json_file(filename: str) -> dict[str, Any]:
    """Load a JSON config file, returning an empty dict if not found."""
    try:
        with open(filename) as f:
            data = json.load(f)
        # Strip comment keys
        return {k: v for k, v in data.items() if not k.startswith("__")}
    except FileNotFoundError:
        log.warning(f"Couldn't find {filename}")
        return {}


class JsonConfigSettingsSource(PydanticBaseSettingsSource):
    """
    Custom pydantic-settings source that loads from defaults.json then config.json.
    Priority (lowest to highest): defaults.json < config.json < env vars.
    """

    def __init__(
        self,
        settings_cls: type[BaseSettings],
        defaults_filename: str = DEFAULTS_FILENAME,
        config_filename: str = CONFIG_FILENAME,
    ) -> None:
        super().__init__(settings_cls)
        self._data: dict[str, Any] = {}
        defaults = _load_json_file(defaults_filename)
        config = _load_json_file(config_filename)
        # config.json overrides defaults.json
        self._data = {**defaults, **config}

    def get_fields_values(self) -> dict[str, Any]:  # type: ignore[override]
        return self._data

    def __call__(self) -> dict[str, Any]:
        return self._data

    def field_is_complex(self, field: Any) -> bool:  # type: ignore[override]
        return False


class NetpalmSettings(BaseSettings):
    """
    Single source of truth for all application configuration.

    Priority order (lowest → highest):
      1. defaults.json
      2. config.json
      3. NETPALM_* environment variables
    """

    model_config = SettingsConfigDict(
        env_prefix="NETPALM_",
        env_ignore_empty=True,
        extra="ignore",
    )

    # API
    api_key: SecretStr = SecretStr("2a84465a-cf38-46b2-9d86-b84Q7d57f288")
    api_key_name: str = "x-api-key"
    cookie_domain: str = "netpalm.local"
    listen_port: int = 9000
    listen_ip: str = "0.0.0.0"
    gunicorn_workers: int = 3
    netpalm_container_name: str = "netpalm-controller"
    netpalm_callback_http_mode: str = "http"

    # PostgreSQL
    database_url: str = "postgresql+asyncpg://netpalm:netpalm@localhost:5432/netpalm"

    # Redis (cache only)
    redis_server: str = "redis"
    redis_port: int = 6379
    redis_key: SecretStr = SecretStr("")
    redis_tls_enabled: bool = False
    redis_tls_cert_file: str = ""
    redis_tls_key_file: str = ""
    redis_tls_ca_cert_file: str = ""
    redis_cache_enabled: bool = True
    redis_cache_default_timeout: int = 300
    redis_cache_key_prefix: str = "NETPALM_RESULT_CACHE"
    redis_update_log: str = "netpalm_extensibles_update_log"
    redis_queue_store: str = "netpalm_queue_store"
    redis_schedule_store: str = "netpalm_schedule_store"
    redis_schedule_store_stats: str = "netpalm_schedule_store_stats"

    # Kafka
    kafka_bootstrap_servers: str = "kafka:9092"
    kafka_fifo_topic: str = "netpalm.jobs.fifo"
    kafka_pinned_topic_prefix: str = "netpalm.jobs.pinned"
    kafka_results_topic: str = "netpalm.results"
    kafka_events_syslog_topic: str = "netpalm.events.syslog"
    kafka_events_snmp_topic: str = "netpalm.events.snmp-trap"
    kafka_consumer_group: str = "netpalm-workers"
    # Legacy topic fields (kept for backward compat)
    kafka_topic_tasks: str = "netpalm.tasks"
    kafka_topic_results: str = "netpalm.results"
    kafka_topic_broadcast: str = "netpalm.broadcast"

    # Scheduler
    scheduler_poll_interval_seconds: int = 5

    # Workers
    fifo_process_per_node: int = 10

    # TextFSM
    txtfsm_index_file: str = "netpalm/backend/plugins/extensibles/ntc-templates/index"
    txtfsm_template_server: str = "http://textfsm.nornir.tech"

    # Paths
    custom_scripts: str = "netpalm/backend/plugins/extensibles/custom_scripts/"
    jinja2_config_templates: str = "netpalm/backend/plugins/extensibles/j2_config_templates/"
    python_service_templates: str = "netpalm/backend/plugins/extensibles/services/"
    ttp_templates: str = "netpalm/backend/plugins/extensibles/ttp_templates/"
    drivers: str = "netpalm/backend/plugins/drivers/"
    event_listeners_dir: str = "netpalm/backend/plugins/event_listeners/"

    # Webhooks
    self_api_call_timeout: int = 15
    default_webhook_url: str = ""
    default_webhook_ssl_verify: bool = True
    default_webhook_timeout: int = 5
    default_webhook_name: str = "default_webhook"
    default_webhook_headers: dict[str, str] = {"Content-Type": "application/json"}
    custom_webhooks: str = "netpalm/backend/plugins/extensibles/custom_webhooks/"
    webhook_jinja2_templates: str = "netpalm/backend/plugins/extensibles/j2_webhook_templates/"

    # Logging
    log_config_filename: str = "config/log-config.yml"

    # Scheduler (legacy APScheduler fields — kept for backward compat)
    apscheduler_num_processes: int = 1
    apscheduler_num_threads: int = 5

    # Security
    device_whitelist: list[str] = []

    # Runtime (not from config file)
    config_filename: str = CONFIG_FILENAME
    worker_name: str = "NOT A WORKER"

    # Computed after init
    whitelist: Optional[DeviceWhitelist] = None

    @field_validator("kafka_bootstrap_servers")
    @classmethod
    def ensure_non_empty_bootstrap(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("kafka_bootstrap_servers must not be empty or whitespace-only")
        return v

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        config_filename = os.getenv("NETPALM_CONFIG", CONFIG_FILENAME)
        json_source = JsonConfigSettingsSource(
            settings_cls,
            defaults_filename=DEFAULTS_FILENAME,
            config_filename=config_filename,
        )
        # Priority (highest first): env vars > config.json/defaults.json > init kwargs
        return (env_settings, json_source, init_settings)

    def model_post_init(self, __context: Any) -> None:
        self.whitelist = DeviceWhitelist(self.device_whitelist)
        self.txtfsm_index_file = self._find_actual_tfsm_path()

    def setup_logging(self, max_debug: bool = False) -> None:
        with open(self.log_config_filename) as infil:
            log_config_dict = yaml.load(infil, Loader=yaml_loader)

        if max_debug:
            for handler in log_config_dict["handlers"].values():
                handler["level"] = "DEBUG"
            for logger in log_config_dict["loggers"].values():
                logger["level"] = "DEBUG"
            log_config_dict["root"]["level"] = "DEBUG"

        logging.config.dictConfig(log_config_dict)
        log.info(f"confload: Logging setup @ {__name__}")

    @property
    def project_root(self) -> str:
        config_file_path = Path(self.config_filename).absolute()
        return str(config_file_path.parent)

    def _find_actual_tfsm_path(self) -> str:
        potentials = [
            self.txtfsm_index_file,
            "netpalm/backend/plugins/extensibles/ntc-templates/index",
            "/code/netpalm/backend/plugins/extensibles/ntc-templates/index",
            "/usr/local/lib/python3.12/site-packages/ntc_templates/templates/index",
        ]
        for potential in potentials:
            if Path(potential).exists():
                return potential
        return self.txtfsm_index_file

    def __call__(self) -> "NetpalmSettings":
        return self


@lru_cache
def get_settings() -> NetpalmSettings:
    """
    Return the singleton NetpalmSettings instance.
    Suitable for FastAPI dependency injection: Depends(get_settings).
    """
    return NetpalmSettings()


# Backward compatibility: existing code that does
#   from netpalm.backend.core.confload.confload import config
# will continue to work.
config = get_settings()

# Also expose Config as an alias for NetpalmSettings for backward compat
Config = NetpalmSettings
