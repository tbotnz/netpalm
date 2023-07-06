import json
import logging
import logging.config
import os
from pathlib import Path

import yaml
import re

from netpalm.backend.core.security.whitelist import DeviceWhitelist

try:
    yaml_loader = yaml.CSafeLoader
except AttributeError:
    yaml_loader = yaml.SafeLoader

log = logging.getLogger(__name__)
CONFIG_FILENAME = "config/config.json"
DEFAULTS_FILENAME = "config/defaults.json"


class ScrubFilter(logging.Filter):
    def __init__(self):
        super(ScrubFilter, self).__init__()

    def filter(self, record):
        # handle msg
        record.msg = self.scrub(record.msg)
        # handle args
        if isinstance(record.args, dict):
            for k in record.args.keys():
                record.args[k] = self.scrub(record.args[k])
        else:
            record.args = tuple(self.scrub(arg) for arg in record.args)

        return True

    def scrub(self, message):
        lookup_table = [
            # {'library': <LibraryName.napalm: 'napalm'>, 'connection_args': {'device_type': 'cisco_ios', 'community': '10.0.2.24', 'username': 'admin', 'password': 'admin'}, 'command': 'show run | i hostname', 'args': {}, 'webhook': {}, 'queue_strategy': <QueueStrategy.pinned: 'pinned'>, 'post_checks': [], 'cache': {}}
            {
                "pattern": r"(?:[aA][sS][sS][wW][oO][rR][dD](?:'|\"): (?:'|\")(.*?)(?:'|\"))",
                "expected_group_index": 1,
            },
            {
                "pattern": r"(?:[oO][kK][eE][nN](?:'|\"): (?:'|\")(.*?)(?:'|\"))",
                "expected_group_index": 1,
            },
            {
                "pattern": r"(?:[kK][eE][yY](?:'|\"): (?:'|\")(.*?)(?:'|\"))",
                "expected_group_index": 1,
            },
            {
                "pattern": r"(?:[eE][cC][rR][eE][tT](?:'|\"): (?:'|\")(.*?)(?:'|\"))",
                "expected_group_index": 1,
            },
            {
                "pattern": r"(?:[oO][mM][uU][nN][iI][tT][yY](?:'|\"): (?:'|\")(.*?)(?:'|\"))",
                "expected_group_index": 1,
            },
        ]
        try:
            result = message
            if type(message) == str:
                for lookup_val in lookup_table:
                    m = re.search(lookup_val["pattern"], result)
                    if m:
                        match_str = m.group(lookup_val["expected_group_index"])
                        result = re.sub(f"{match_str}", "******", result)
        except Exception as e:
            pass
        return result


def load_config_files(
    defaults_filename: str = DEFAULTS_FILENAME, config_filename: str = CONFIG_FILENAME
) -> dict:
    data = {}

    for fname in (defaults_filename, config_filename):
        try:
            with open(fname) as infil:
                data.update(json.load(infil))
        except FileNotFoundError:
            log.warning(f"Couldn't find {fname}")

    if not data:
        raise RuntimeError(
            f"Could not find either {defaults_filename} or {config_filename}"
        )

    return data


class Config:
    def __init__(self, config_filename=None, search_tfsm=True):
        if config_filename is None:
            config_filename = CONFIG_FILENAME

        data = load_config_files(DEFAULTS_FILENAME, config_filename)
        self.data = data

        self.listen_ip = data["listen_ip"]
        self.listen_port = data["listen_port"]
        self.netpalm_container_name = data["netpalm_container_name"]
        self.netpalm_callback_http_mode = data["netpalm_callback_http_mode"]
        self.api_key = data["api_key"]
        self.api_key_name = data["api_key_name"]
        self.cookie_domain = data["cookie_domain"]
        self.redis_task_ttl = data["redis_task_ttl"]
        self.redis_task_result_ttl = data["redis_task_result_ttl"]
        self.redis_server = data["redis_server"]
        self.redis_port = data["redis_port"]
        self.redis_key = data["redis_key"]
        self.redis_core_q = data["redis_core_q"]
        self.redis_fifo_q = data["redis_fifo_q"]
        self.redis_broadcast_q = data["redis_broadcast_q"]
        self.redis_queue_store = data["redis_queue_store"]
        self.redis_pinned_store = data["redis_pinned_store"]
        self.redis_schedule_store = data["redis_schedule_store"]
        self.redis_schedule_store_stats = data["redis_schedule_store_stats"]
        self.redis_cache_enabled = data["redis_cache_enabled"]
        self.redis_cache_default_timeout = data["redis_cache_default_timeout"]
        self.redis_cache_key_prefix = data["redis_cache_key_prefix"]
        self.redis_update_log = data["redis_update_log"]
        self.redis_tls_cert_file = data["redis_tls_cert_file"]
        self.redis_tls_key_file = data["redis_tls_key_file"]
        self.redis_tls_ca_cert_file = data["redis_tls_ca_cert_file"]
        self.redis_tls_enabled = data["redis_tls_enabled"]
        self.redis_socket_connect_timeout = data["redis_socket_connect_timeout"]
        self.redis_socket_keepalive = data["redis_socket_keepalive"]
        self.fifo_process_per_node = data["fifo_process_per_node"]
        self.pinned_process_per_node = data["pinned_process_per_node"]
        self.redis_task_timeout = data["redis_task_timeout"]
        self.txtfsm_index_file = data["txtfsm_index_file"]
        self.txtfsm_template_server = data["txtfsm_template_server"]
        self.custom_scripts = data["custom_scripts"]
        self.jinja2_config_templates = data["jinja2_config_templates"]
        self.python_service_templates = data["python_service_templates"]
        self.self_api_call_timeout = data["self_api_call_timeout"]
        self.default_webhook_url = data["default_webhook_url"]
        self.default_webhook_ssl_verify = data["default_webhook_ssl_verify"]
        self.default_webhook_timeout = data["default_webhook_timeout"]
        self.default_webhook_name = data["default_webhook_name"]
        self.default_webhook_headers = data["default_webhook_headers"]
        self.custom_webhooks = data["custom_webhooks"]
        self.webhook_jinja2_templates = data["webhook_jinja2_templates"]
        self.log_config_filename = data["log_config_filename"]
        self.ttp_templates = data["ttp_templates"]
        self.mongo_server_ip = data["mongo_server_ip"]
        self.mongo_server_port = data["mongo_server_port"]
        self.mongo_user = data["mongo_user"]
        self.mongo_password = data["mongo_password"]
        self.apscheduler_num_processes = data["apscheduler_num_processes"]
        self.apscheduler_num_threads = data["apscheduler_num_threads"]
        self.whitelist = DeviceWhitelist(data.get("device_whitelist"))
        self.drivers = data["drivers"]
        self.worker_name = "NOT A WORKER"  # Worker objects will record this here so that it can be referenced elsewhere

        # load tls
        try:
            log.info(f"confload: opening TLS files")
            tls_files = [
                self.redis_tls_cert_file,
                self.redis_tls_key_file,
                self.redis_tls_ca_cert_file,
            ]
            for tlsf in tls_files:
                with open(tlsf) as f:
                    tlsf = f
        except FileNotFoundError:
            log.info(f"confload: error opening TLS files")

        def envvar_as_bool(var):
            if var.upper() in ["TRUE", "YES"]:
                return True
            if var.upper() in ["FALSE", "NO"]:
                return False
            return var

        for key in self.__dict__:  # Check for environment variables
            envvar_key = f"NETPALM_{key.upper()}"
            if value := os.getenv(envvar_key):
                if type(getattr(self, key)) is int:
                    setattr(self, key, int(value))
                setattr(self, key, envvar_as_bool(value))
        # this is AFTER the envvar loop on purpose.  Everything down here overrides envvars
        self.config_filename = config_filename
        if search_tfsm:
            self.txtfsm_index_file = self.find_actual_tfsm_path()

    def setup_logging(self, max_debug=False):
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
    def project_root(self):
        config_file_path = Path(self.config_filename).absolute()
        return str(config_file_path.parent)

    def find_actual_tfsm_path(self):
        potentials = [
            "netpalm/backend/plugins/extensibles/ntc-templates/index",
            "/code/netpalm/backend/plugins/extensibles/ntc-templates/index",
            "/usr/local/lib/python3.8/site-packages/ntc_templates/templates/index",
        ]
        potentials.insert(0, self.txtfsm_index_file)
        for potential in potentials:
            if Path(potential).exists():
                return potential

        # raise FileNotFoundError(f"confload: Can't find TextFSM Index file in any of {potentials}")

    def __call__(self):
        return self


# this indirection helps w/ testing, also compatibility with existing code that uses `config().attribute`
def initialize_config(search_tfsm: bool = True):
    return Config(os.getenv("NETPALM_CONFIG"), search_tfsm=search_tfsm)


config = initialize_config()
