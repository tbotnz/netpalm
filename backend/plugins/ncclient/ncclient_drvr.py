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
        
    def connect(self):
        try:
            conn = manager.connect(host=self.host, port=830, username=self.username, password=self.password, hostkey_verify=False, device_params={'name':self.driver})
            return conn
        except Exception as e:
            return str(e)

    def getconfig(self, session=False, command=False):
        try:
            result = {}
            if self.kwarg:
                response = session.get_config(**self.kwarg).data_xml
                respdict = xmltodict.parse(response)
                if respdict:
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
                print(response)
                respdict = xmltodict.parse(response)
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
