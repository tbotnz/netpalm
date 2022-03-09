import time
import json

from typing import Any

from netpalm.backend.core.redis.rediz import Rediz
from fastapi.encoders import jsonable_encoder

from netpalm.backend.core.models.models import GetConfig
from netpalm.backend.core.models.napalm import NapalmGetConfig
from netpalm.backend.core.models.ncclient import NcclientGet
from netpalm.backend.core.models.ncclient import NcclientGetConfig
from netpalm.backend.core.models.netmiko import NetmikoGetConfig
from netpalm.backend.core.models.puresnmp import PureSNMPGetConfig
from netpalm.backend.core.models.restconf import Restconf

from netpalm.backend.core.models.models import SetConfig
from netpalm.backend.core.models.napalm import NapalmSetConfig
from netpalm.backend.core.models.ncclient import NcclientSetConfig
from netpalm.backend.core.models.netmiko import NetmikoSetConfig
from netpalm.backend.core.models.restconf import Restconf
from netpalm.backend.core.models.task import Response, ResponseBasic

from netpalm.backend.core.models.service import ServiceInstanceData, ServiceInstanceState
from netpalm.backend.core.models.task import ServiceResponse, Response

from netpalm.backend.core.models.models import Script

from netpalm.backend.core.models.task import Response

from netpalm.backend.plugins.utilities.webhook.webhook import exec_webhook_func


class NetpalmManager(Rediz):

    def _get_config(self, getcfg: GetConfig, library: str = None) -> Response:
        """ executes the base netpalm getconfig method async and returns the task id response obj """
        if isinstance(getcfg, dict):
            req_data = getcfg
        else:
            req_data = getcfg.dict(exclude_none=True)
        if library is not None:
            req_data["library"] = library
        r = self.execute_task(method="getconfig", kwargs=req_data)
        resp = jsonable_encoder(r)
        return resp

    def get_config_netmiko(self, getcfg: NetmikoGetConfig):
        """ executes the netpalm netmiko getconfig method async and returns the response obj """
        return self._get_config(getcfg, library="netmiko")

    def get_config_napalm(self, getcfg: NapalmGetConfig):
        """ executes the netpalm napalm getconfig method async and returns the response obj """
        return self._get_config(getcfg, library="napalm")

    def get_config_puresnmp(self, getcfg: PureSNMPGetConfig):
        """ executes the netpalm puresnmp getconfig method async and returns the response obj """
        return self._get_config(getcfg, library="puresnmp")

    def get_config_ncclient(self, getcfg: NcclientGetConfig):
        """ executes the netpalm ncclient getconfig method async and returns the response obj """
        return self._get_config(getcfg, library="ncclient")

    def get_config_restconf(self, getcfg: Restconf):
        """ executes the netpalm restconf getconfig method async and returns the response obj """
        return self._get_config(getcfg, library="restconf")

    def ncclient_get(self, getcfg: NcclientGet, library: str = "ncclient"):
        """
        ncclient Manager.get() rpc call
        Certain device types dont have rpc methods defined in ncclient.
        This is a work around for that.
        """
        if isinstance(getcfg, dict):
            req_data = getcfg
        else:
            req_data = getcfg.dict(exclude_none=True)

        if library is not None:
            req_data["library"] = library
        r = self.execute_task(method="ncclient_get", kwargs=req_data)
        resp = jsonable_encoder(r)
        return resp

    def _set_config(self, setcfg: SetConfig, library: str = None) -> Response:
        """ executes the base netpalm setconfig method async and returns the task id response obj """
        if isinstance(setcfg, dict):
            req_data = setcfg
        else:
            req_data = setcfg.dict(exclude_none=True)
        if library is not None:
            req_data["library"] = library
        r = self.execute_task(method="setconfig", kwargs=req_data)
        resp = jsonable_encoder(r)
        return resp

    def set_config_dry_run(self, setcfg: SetConfig):
        """ executes the netpalm setconfig dry run method async and returns the response obj """
        if isinstance(setcfg, dict):
            req_data = setcfg
        else:
            req_data = setcfg.dict(exclude_none=True)
        r = self.execute_task(method="dryrun", kwargs=req_data)
        resp = jsonable_encoder(r)
        return resp

    def set_config_netmiko(self, setcfg: NetmikoSetConfig):
        """ executes the netmiko setconfig method async and returns the response obj """
        return self._set_config(setcfg, library="netmiko")

    def set_config_napalm(self, setcfg: NapalmSetConfig):
        """ executes the napalm setconfig method async and returns the response obj """
        return self._set_config(setcfg, library="napalm")

    def set_config_ncclient(self, setcfg: NcclientSetConfig):
        """ executes the ncclient setconfig method async and returns the response obj """
        return self._set_config(setcfg, library="ncclient")

    def set_config_restconf(self, setcfg: Restconf):
        """ executes the restconf setconfig method async and returns the response obj """
        return self._set_config(setcfg, library="restconf")

    def execute_script(self, script: Script):
        """ executes the netpalm script method async and returns the response obj """
        if isinstance(script, dict):
            req_data = script
        else:
            req_data = script.dict(exclude_none=True)

        # check if pinned required
        if req_data.get("queue_strategy") == "pinned":
            if isinstance(req_data.get("connection_args"), dict):
                req_data["connection_args"]["host"] = req_data["script"]
            else:
                req_data["connection_args"] = {}
                req_data["connection_args"]["host"] = req_data["script"]

        r = self.execute_task(method="script", kwargs=req_data)
        resp = jsonable_encoder(r)
        return resp

    def create_new_service_instance(self, service_model: str, service: Any):
        """ creates a netpalm service and adds it to the service inventory """
        if isinstance(service, dict):
            req_data = service
        else:
            req_data = service.dict(exclude_none=True)
        r = self.execute_create_service_task(metho="service_create", model=service_model, kwargs=req_data)
        resp = jsonable_encoder(r)
        return resp

    def list_service_instances(self):
        """ lists services in the netpalm service inventory """
        r = self.get_service_instances()
        if r:
            formatted_result = ResponseBasic(status="success", data={"task_result": r}).dict()
        else:
            formatted_result = ResponseBasic(status="success", data={"task_result": None}).dict()
        resp = jsonable_encoder(formatted_result)
        return resp

    def get_service_instance(self, service_id: str):
        """ gets a from the service inventory """
        r = self.fetch_service_instance_args(sid=service_id)
        if r:
            formatted_result = ResponseBasic(status="success", data={"task_result": r}).dict()
            resp = jsonable_encoder(formatted_result)
            return resp
        else:
            return False

    def validate_service_instance_state(self, service_id: str):
        """ runs the validate method on the service template """
        r = self.validate_service_instance(sid=service_id)
        resp = jsonable_encoder(r)
        return resp

    def health_check_service_instance_state(self, service_id: str):
        """ runs the validate method on the service template """
        r = self.health_check_service_instance(sid=service_id)
        resp = jsonable_encoder(r)
        return resp

    def retrieve_service_instance_state(self, service_id: str):
        """ retrieves the service current state """
        r = self.retrieve_service_instance(sid=service_id)
        resp = jsonable_encoder(r)
        return resp

    def redeploy_service_instance_state(self, service_id: str):
        """ redeploys the service instance """
        self.set_service_instance_status(self.service_id, state="deploying")
        r = self.redeploy_service_instance(sid=service_id)
        resp = jsonable_encoder(r)
        return resp

    def delete_service_instance_state(self, service_id: str):
        """ deletes the service instance """
        r = self.delete_service_instance(sid=service_id)
        resp = jsonable_encoder(r)
        return resp

    def update_service_instance(self, service_id: str, service_data: Any):
        """ deletes the service instance """

        if isinstance(service_data, dict):
            req_data = service_data
        else:
            req_data = service_data.dict(exclude_none=True)

        data = self.fetch_service_instance(service_id)
        if data:
            service_json = json.loads(data)
            service_json["service_data"] = req_data
            service_json["service_meta"]["service_state"] = "deploying"
            self.update_service_instance_data(service_id, service_json)
        r = self.execute_task(method="service_update", kwargs=service_json)
        resp = jsonable_encoder(r)
        return resp

    def retrieve_task_result(self, netpalm_response: Response):
        """ waits for the task to complete the returns the result """
        if isinstance(netpalm_response, dict):
            req_data = netpalm_response
        else:
            req_data = netpalm_response.dict(exclude_none=True)

        if req_data["status"] == "success":
            task_id = req_data["data"]["task_id"]

            while True:
                r = self.fetchtask(task_id=task_id)
                if (r["data"]["task_status"] == "finished") or (r["data"]["task_status"] == "failed"):
                    return r
                time.sleep(0.3)
        else:
            return req_data

    def retrieve_task_result_multiple(self, netpalm_response_list: list):
        """
            retrieves multiple task results in a sync fashion

            Args:
                netpalm_response_list: list of netpalm response objects


            Returns:
                list of netpalm responses objects with result
        """

        result = []
        for netpalm_response in netpalm_response_list:
            one_result = self.retrieve_task_result(netpalm_response)
            result.append(one_result)

        return result

    def trigger_webhook(self, webhook_payload: dict, webhook_meta_data: dict):
        """
            executes a webhook call

            can also run the job_data through a j2 template if the j2template name is specificed in the

            Args:
                webhook_payload: dictionary containing the result of the job to be passed into the webhook e.g a netpalm Response dict
                webhook_meta_data: This is a dictionary describing the metadata of webhook itself e.g webhook name, user specified args to pass into the webhook itself
                        {
                            "name": "default_webhook", # webhook name
                            "args": {
                                "insert": "something useful" # args to pass into webhook
                            },
                            "j2template": "myj2template" # add this key if you want to run the job data through a j2template before passing it into the webhook
                        }

            Returns:
                the result of executing the webhook
        """
        res = exec_webhook_func(jobdata=webhook_payload, webhook_payload=webhook_meta_data)
        return res
