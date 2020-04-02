import json

class config:
    
    def __init__(self):
        with open("config.json") as json_file:
            data = json.load(json_file)
            self.listen_ip = data["listen_ip"]
            self.listen_port = data["listen_port"]
            self.apikey = data["apikey"]
            self.redis_task_ttl = data["redis_task_ttl"]
            self.redis_server = data["redis_server"]
            self.redis_port = data["redis_port"]
            self.redis_core_q = data["redis_core_q"]
            self.redis_task_timeout = data["redis_task_timeout"]
            self.txtfsm_index_file = data["txtfsm_index_file"]
            self.txtfsm_template_server = data["txtfsm_template_server"]
            self.custom_scripts = data["custom_scripts"]
            self.jinja2_templates = data["jinja2_templates"]
