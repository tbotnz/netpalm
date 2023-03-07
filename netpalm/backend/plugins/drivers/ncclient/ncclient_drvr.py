import xmltodict
import logging
from ncclient import manager

from netpalm.backend.core.utilities.rediz_meta import (
    write_meta_error_string,
    write_meta_error,
)
from netpalm.backend.core.driver.netpalm_driver import NetpalmDriver

log = logging.getLogger(__name__)


class ncclien(NetpalmDriver):
    driver_name = "ncclient"

    def __init__(self, **kwargs):
        self.kwarg = kwargs.get("args", False)
        self.connection_args = kwargs.get("connection_args", False)

    def connect(self):
        try:
            conn = manager.connect(**self.connection_args)
            return conn
        except Exception as e:
            write_meta_error(e)

    @staticmethod
    def __get_capabilities(session=False):
        try:
            capabilities = session.server_capabilities
            return capabilities
        except Exception as e:
            write_meta_error(e)

    def getmethod(self, session=False, command=False):
        try:
            result = {}
            if self.kwarg:
                rjsflag = False
                if "render_json" in self.kwarg:
                    if self.kwarg.get("render_json"):
                        rjsflag = True
                    del self.kwarg["render_json"]
                response = session.get(**self.kwarg).data_xml
                if rjsflag:
                    respdict = xmltodict.parse(response)
                    if respdict:
                        result["get_config"] = respdict
                    else:
                        write_meta_error_string("failed to parse response")
                else:
                    result["get_config"] = response
            else:
                write_meta_error_string("args are required")
            return result
        except Exception as e:
            write_meta_error(e)

    def sendcommand(self, session=False, command=False):
        try:
            result = {}
            if self.kwarg:
                rjsflag = False

                if "render_json" in self.kwarg:
                    if self.kwarg.get("render_json"):
                        rjsflag = True
                    del self.kwarg["render_json"]

                if "capabilities" in self.kwarg:
                    if self.kwarg.get("capabilities"):
                        result["capabilities"] = self.__get_capabilities(
                            session=session
                        )
                    del self.kwarg["capabilities"]

                # check whether RPC required
                if self.kwarg.get("rpc", False):
                    response = session.rpc(**self.kwarg).data_xml
                # else a standard get_config method call
                else:
                    response = session.get_config(**self.kwarg).data_xml
                if rjsflag:
                    respdict = xmltodict.parse(response)
                    if respdict:
                        result["get_config"] = respdict
                    else:
                        write_meta_error_string("failed to parse response")
                else:
                    result["get_config"] = response
            else:
                write_meta_error_string("args are required")
            return result
        except Exception as e:
            write_meta_error(e)

    def editconfig(self, session=False, dry_run=False):
        try:
            result = {}
            if self.kwarg:
                rjsflag = False
                if "render_json" in self.kwarg:
                    if self.kwarg.get("render_json"):
                        rjsflag = True
                    del self.kwarg["render_json"]
                # edit_config returns an RPCReply object which doesnt have a
                # data_xml property. Fixes 'Unserializable return value'
                # message from rq.job:restore
                response = session.edit_config(**self.kwarg).xml
                if dry_run:
                    session.discard_changes()
                else:
                    session.commit()
                if rjsflag:
                    respdict = xmltodict.parse(response)
                    if respdict:
                        result["edit_config"] = respdict
                    else:
                        write_meta_error_string("failed to parse response")
                else:
                    result["edit_config"] = response
            else:
                write_meta_error_string("args are required")
            return result
        except Exception as e:
            write_meta_error(e)

    def logout(self, session):
        try:
            response = session.close_session()
            return response
        except Exception as e:
            write_meta_error(e)
