from ncclient import manager
from lxml import etree
import xmltodict
import json

class ncclien:

    def __init__(self, **kwargs):
        self.username = kwargs.get('username', False)
        self.password = kwargs.get('password', False)
        self.driver = kwargs.get('driver', False)
        self.host = kwargs.get('host', False)
        self.kwarg = kwargs.get('args', False)
        self.connection_args = kwargs.get('connection_args', False)     

    def connect(self):
        try:
            conn = manager.connect(**self.connection_args)
            return conn
        except Exception as e:
            return e

    def getconfig(self, session=False, command=False):
        try:
            result = {}
            if self.kwarg:
                render_json = self.kwarg.get("render_json", False)
                rjsflag = False
                if render_json:
                    del self.kwarg["render_json"]
                    rjsflag = True
                response = session.get_config(**self.kwarg).data_xml
                if rjsflag:
                    respdict = xmltodict.parse(response)
                    if respdict:
                        result["get_config"] = respdict
                    else:
                        raise Exception("no response")
                else:
                    result["get_config"] = response
            else:
                raise Exception('args are required')
            return result
        except Exception as e:
            return str(e)

    def editconfig(self, session=False):
        try:
            result = {}
            if self.kwarg:
                response = session.edit_config(**self.kwarg)
                if respdict:
                    result["edit_config"] = response
            else:
                raise Exception('args are required')
            return result
        except Exception as e:
            return str(e)

    def logout(self, session):
        try:
            response = session.close_session()
            return response
        except Exception as e:
            return str(e)
