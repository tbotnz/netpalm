import json

class config:
    
    def __init__(self):
        with open("config.json") as json_file:
            data = json.load(json_file)
            self.listen_ip = data["listen_ip"]
            self.listen_port = data["listen_port"]
            self.api_key = data["api_key"]
            self.api_key_name = data["api_key_name"]
            self.cookie_domain = data["cookie_domain"]
            self.redis_task_ttl = data["redis_task_ttl"]
            self.redis_server = data["redis_server"]
            self.redis_port = data["redis_port"]
            self.redis_key = data["redis_key"]
            self.redis_core_q = data["redis_core_q"]
            self.redis_fifo_q = data["redis_fifo_q"]
            self.redis_queue_store = data["redis_queue_store"]
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

