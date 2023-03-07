from puresnmp import puresnmp

from netpalm.backend.core.core.driver.netpalm_driver import NetpalmDriver
from netpalm.backend.core.utilities.rediz_meta import write_meta_error


class pursnmp(NetpalmDriver):
    driver_name = "puresnmp"

    def __init__(self, **kwargs):
        self.connection_args = kwargs.get("connection_args", False)
        if "port" not in self.connection_args.keys():
            self.connection_args["port"] = 161
        if "timeout" not in self.connection_args.keys():
            self.connection_args["timeout"] = 2
        self.input_args = kwargs.get("args", False)
        if "type" not in self.input_args.keys() or not self.input_args:
            self.input_args = {}
            self.input_args["type"] = "get"

    def connect(self):
        try:
            return True
        except Exception as e:
            write_meta_error(e)

    def sendcommand(self, session=False, command=False):
        try:
            result = {}
            for c in command:
                # remove timeout weirdness for tables
                if self.input_args["type"] == "table":
                    response = getattr(puresnmp, self.input_args["type"])(
                        ip=self.connection_args["host"],
                        community=self.connection_args["community"],
                        oid=c,
                        port=self.connection_args["port"],
                    )
                else:
                    response = getattr(puresnmp, self.input_args["type"])(
                        ip=self.connection_args["host"],
                        community=self.connection_args["community"],
                        oid=c,
                        port=self.connection_args["port"],
                        timeout=self.connection_args["timeout"],
                    )

                # remnder result data for get call
                if self.input_args["type"] == "get":
                    if isinstance(response, bytes):
                        response = response.decode(errors="ignore")
                    result[c] = response
                # remnder result data for walk call
                elif self.input_args["type"] == "walk":
                    result[c] = []
                    for row in response:
                        oid = str(row[0])
                        oid_raw = row[1]
                        if isinstance(oid_raw, bytes):
                            oid_raw = oid_raw.decode(errors="ignore")
                        result[c].append({oid: oid_raw})
                # remnder result data for table call
                elif self.input_args["type"] == "table":
                    result[c] = []
                    for key in response[0]:
                        oid = str(key)
                        oid_raw = response[0][key]
                        if isinstance(response[0][key], bytes):
                            oid_raw = oid_raw.decode(errors="ignore")
                        result[c].append({oid: oid_raw})
                else:
                    result[c] = f"{response}"
            return result
        except Exception as e:
            write_meta_error(e)

    def config(self, session=False, command=False, dry_run=False):
        try:
            return True
        except Exception as e:
            write_meta_error(e)

    def logout(self, session):
        try:
            return True
        except Exception as e:
            write_meta_error(e)
