from puresnmp import get, set

from netpalm.backend.core.utilities.rediz_meta import write_meta_error


class pursnmp:

    def __init__(self, **kwargs):
        self.connection_args = kwargs.get("connection_args", False)
        if "port" not in self.connection_args.keys():
            self.connection_args["port"] = 161
        if "timeout" not in self.connection_args.keys():
            self.connection_args["timeout"] = 2

    def connect(self):
        try:
            return True
        except Exception as e:
            write_meta_error(f"{e}")

    def sendcommand(self, session=False, command=False):
        try:
            result = {}
            for c in command:
                response = get(
                               ip=self.connection_args["host"],
                               community=self.connection_args["community"],
                               oid=c,
                               port=self.connection_args["port"],
                               timeout=self.connection_args["timeout"],
                               )
                result[c] = response
            return result
        except Exception as e:
            write_meta_error(f"{e}")

    def config(self, session=False, command=False, dry_run=False):
        try:
            return True
        except Exception as e:
            write_meta_error(f"{e}")

    def logout(self, session):
        try:
            return True
        except Exception as e:
            write_meta_error(f"{e}")
