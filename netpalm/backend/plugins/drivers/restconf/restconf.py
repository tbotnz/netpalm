import json

import requests

from netpalm.backend.core.utilities.rediz_meta import write_meta_error

from netpalm.backend.core.core.driver.netpalm_driver import NetpalmDriver


class restconf(NetpalmDriver):
    driver_name = "restconf"

    def __init__(self, **kwargs):
        self.connection_args = kwargs.get("connection_args", False)
        self.host = self.connection_args.get("host", False)
        del self.connection_args["host"]
        self.kwarg = kwargs.get("args", False)
        self.port = self.connection_args.get("port", False)
        del self.connection_args["port"]
        self.default_headers = {
            "Content-Type": "application/vnd.yang.data+json",
            "Accept": "application/vnd.yang.data+json",
        }
        self.username = self.connection_args.get("username", False)
        del self.connection_args["username"]
        self.password = self.connection_args.get("password", False)
        del self.connection_args["password"]
        self.headers = self.connection_args.get("headers", False)
        self.transport = self.connection_args.get("transport", False)
        del self.connection_args["transport"]
        self.action = self.kwarg.get("action", False)
        self.payload = self.kwarg.get("payload", False)
        self.params = self.kwarg.get("params", False)

    def connect(self):
        try:
            if not self.headers:
                self.headers = self.default_headers
            else:
                del self.connection_args["headers"]
            return True
        except Exception as e:
            write_meta_error(e)

    def sendcommand(self, session=False, command=False):
        try:
            # restconf get call
            result = {}
            url = (
                self.transport
                + "://"
                + self.host
                + ":"
                + str(self.port)
                + self.kwarg["uri"]
            )
            response = requests.get(
                url,
                auth=(self.username, self.password),
                params=self.params,
                headers=self.headers,
                **self.connection_args
            )
            try:
                res = json.loads(response.text)
            except Exception:
                res = ""
                pass
            result[url] = {}
            result[url]["status_code"] = response.status_code
            result[url]["result"] = res
            return result
        except Exception as e:
            write_meta_error(e)

    def config(self, session=False, command=False):
        try:
            result = {}
            url = (
                self.transport
                + "://"
                + self.host
                + ":"
                + str(self.port)
                + self.kwarg["uri"]
            )
            if hasattr(requests, str(self.action)):
                response = getattr(requests, str(self.action))(
                    url,
                    auth=(self.username, self.password),
                    data=json.dumps(self.payload),
                    params=self.params,
                    headers=self.headers,
                    **self.connection_args
                )
                try:
                    res = json.loads(response.text)
                except Exception:
                    res = ""
                    pass
                result[url] = {}
                result[url]["status_code"] = response.status_code
                result[url]["result"] = res
                return result
            else:
                raise Exception(self.action + " not found in requests")
        except Exception as e:
            write_meta_error(e)

    def logout(self, session):
        try:
            return True
        except Exception as e:
            write_meta_error(e)
