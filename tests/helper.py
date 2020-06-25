import requests
import json
import time

class netpalm_testhelper:

    def __init__(self):
        with open("../config.json") as json_file:
            data = json.load(json_file)
        self.apikey = data["apikey"]
        self.ip = data["listen_ip"]
        self.port = data["listen_port"]
        self.headers = {'Content-type': 'application/json', 'Accept': 'text/plain', 'x-api-key': self.apikey}
        # test devices go here
        self.test_device_ios_cli = "10.0.2.30"
        self.test_device_netconf = "10.0.2.39"
        self.test_device_restconf = "10.0.2.40"

    def check_task(self, taskid):
        try:
            r = requests.get('http://'+self.ip+':'+str(self.port)+'/task/'+taskid,headers=self.headers)
            return r.json()
        except Exception as e:
            return False

    def poll_task(self, taskid):
        try:
            task_complete = False
            result = False
            while task_complete == False:
                task_res = self.check_task(taskid)
                if task_res["data"]["task_status"] == "finished":
                    result = task_res["data"]["task_result"]
                    task_complete = True
            return result
        except Exception as e:
            return False

    def post_and_check(self, url, payload):
        try:
            r = requests.post('http://'+self.ip+':'+str(self.port)+url, json=payload, headers=self.headers)
            task = r.json()["data"]["task_id"]
            result = self.poll_task(task)
            return result
        except Exception as e:
            return e
