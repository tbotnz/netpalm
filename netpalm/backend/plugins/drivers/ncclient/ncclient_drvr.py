import xmltodict
import logging
from ncclient import manager

from netpalm.backend.core.utilities.rediz_meta import write_meta_error

log = logging.getLogger(__name__)


class ncclien:

    def __init__(self, **kwargs):
        self.kwarg = kwargs.get("args", False)
        self.connection_args = kwargs.get("connection_args", False)

    def connect(self):
        try:
            log.info(self.connection_args)
            conn = manager.connect(**self.connection_args)
            return conn
        except Exception as e:
            write_meta_error(f"{e}")

    def getconfig(self, session=False, command=False):
        try:
            result = {}
            if self.kwarg:
                render_json = self.kwarg.get("render_json", False)
                rjsflag = False
                if render_json:
                    del self.kwarg["render_json"]
                    rjsflag = True
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
                        write_meta_error("no response")
                else:
                    result["get_config"] = response
            else:
                write_meta_error("args are required")
            return result
        except Exception as e:
            write_meta_error(f"{e}")

    def editconfig(self, session=False, dry_run=False):
        try:
            result = {}
            if self.kwarg:
                response = session.edit_config(**self.kwarg)
                if dry_run:
                    session.discard_changes()
                else:
                    session.commit()
                if response:
                    result["edit_config"] = response
            else:
                write_meta_error("args are required")
            return result
        except Exception as e:
            write_meta_error(f"{e}")

    def logout(self, session):
        try:
            response = session.close_session()
            return response
        except Exception as e:
            write_meta_error(f"{e}")
