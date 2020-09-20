import json
import logging
import logging.config
import os
from pathlib import Path

import yaml

try:
    yaml_loader = yaml.CSafeLoader
except AttributeError:
    yaml_loader = yaml.SafeLoader


log = logging.getLogger(__name__)
DEFAULT_FILENAME = "config/config.json"


class Config:
    def __init__(self, config_filename=None, search_tfsm=True):
        if config_filename is None:
            config_filename = DEFAULT_FILENAME

        with open(config_filename) as json_file:
            data = json.load(json_file)

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
        self.jinja2_service_templates = data["jinja2_service_templates"]
        self.self_api_call_timeout = data["self_api_call_timeout"]
        self.default_webhook_url = data["default_webhook_url"]
        self.default_webhook_ssl_verify = data["default_webhook_ssl_verify"]
        self.default_webhook_timeout = data["default_webhook_timeout"]
        self.default_webhook_name = data["default_webhook_name"]
        self.default_webhook_headers = data["default_webhook_headers"]
        self.custom_webhooks = data["custom_webhooks"]
        self.webhook_jinja2_templates = data["webhook_jinja2_templates"]
        self.log_config_filename = data["log_config_filename"]

        #load tls
        try:
            log.info(f"confload: opening TLS files")
            tls_files = [self.redis_tls_cert_file, self.redis_tls_key_file, self.redis_tls_ca_cert_file]
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
            "/usr/local/lib/python3.8/site-packages/ntc_templates/templates/index"
        ]
        potentials.insert(0, self.txtfsm_index_file)
        for potential in potentials:

            if Path(potential).exists():
                return potential
        raise FileNotFoundError(f"confload: Can't find TextFSM Index file in any of {potentials}")

    def __call__(self):
        return self


# this indirection helps w/ testing, also compatibility with existing code that uses `config().attribute`
def initialize_config(search_tfsm: bool = True):
    return Config(os.getenv("NETPALM_CONFIG"), search_tfsm=search_tfsm)


config = initialize_config()
