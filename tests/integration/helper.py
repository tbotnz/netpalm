import json
import logging
import time

import requests
from typing import Dict, Tuple, List

log = logging.getLogger(__name__)
CONFIG_FILENAME = "config/config.json"
DEFAULTS_FILENAME = "config/defaults.json"


def load_config_files(defaults_filename: str = DEFAULTS_FILENAME, config_filename: str = CONFIG_FILENAME) -> dict:
    data = {}

    for fname in (defaults_filename, config_filename):
        try:
            with open(fname) as infil:
                data.update(json.load(infil))
        except FileNotFoundError:
            log.warning(f"Couldn't find {fname}")

    if not data:
        raise RuntimeError(f"Could not find either {defaults_filename} or {config_filename}")

    return data


class NetpalmTestHelper:

    def __init__(self):
        data = load_config_files()
        self.apikey = data["api_key"]
        self.ip = '127.0.0.1'
        self.port = data["listen_port"]
        self.base_url = f"http://{self.ip}:{self.port}"
        self.headers = {'Content-type': 'application/json', 'Accept': 'text/plain', 'x-api-key': self.apikey}
        # test devices go here
        self.test_device_ios_cli = "10.0.2.33"
        self.test_device_netconf = "10.0.2.39"
        self.test_device_restconf = "ios-xe-mgmt-latest.cisco.com"
        self.test_device_cisgo = "cisgo"
        self.http_timeout = 5
        self.task_timeout = 15
        self.task_poll_interval = 0.2

    def get(self, endpoint: str):
        try:
            r = requests.get(f"http://{self.ip}:{self.port}/{endpoint}",
                             headers=self.headers, timeout=self.http_timeout)
            return r.json()
        except Exception as e:
            log.exception(f"error while getting {endpoint}")
            raise

    def post(self, endpoint: str, data):
        try:
            r = requests.post(f"http://{self.ip}:{self.port}/{endpoint}",
                              headers=self.headers, json=data, timeout=self.http_timeout)
            return r.json()
        except Exception as e:
            log.exception(f"error while posting to {endpoint}")
            raise

    def check_task(self, taskid):
        return self.get(f"task/{taskid}")

    def poll_task(self, taskid, timeout=None) -> Tuple[Dict, List]:
        if timeout is None:
            timeout = self.task_timeout

        start_time = time.time()
        while True:
            task_res = self.check_task(taskid)
            if task_res["data"]["task_status"] == "finished" or task_res["data"]["task_status"] == "failed":
                result, errors = task_res["data"]["task_result"], task_res["data"]["task_errors"]
                break

            if time.time() + self.task_poll_interval > start_time + timeout:
                raise TimeoutError("Netmiko task timed out")

            time.sleep(self.task_poll_interval)

        log.error(f'got {task_res}')
        return result, errors

    def poll_task_errors(self, taskid, timeout=None) -> List:
        result, errors = self.poll_task(taskid, timeout)
        return errors

    def post_and_check(self, endpoint, payload) -> Dict:
        url = f"{self.base_url}{endpoint}"
        r = requests.post(url, json=payload, headers=self.headers, timeout=self.http_timeout)
        task_id = r.json()["data"]["task_id"]
        result, errors = self.poll_task(task_id)
        return result

    def post_and_check_errors(self, endpoint, payload) -> List:
        url = f"{self.base_url}{endpoint}"
        r = requests.post(url, json=payload, headers=self.headers, timeout=self.http_timeout)
        task_id = r.json()["data"]["task_id"]
        errors = self.poll_task_errors(task_id)
        return errors

    def check_many(self, payload) -> List[Dict]:
        results = []
        for task in payload:
            res, err = self.poll_task(task["data"]["data"]["task_id"])
            results.append(res)
        return results