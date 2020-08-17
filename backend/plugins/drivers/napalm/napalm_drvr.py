import napalm

from backend.core.meta.rediz_meta import write_meta_error


class naplm:

    def __init__(self, connection_args: dict):
        self.connection_args = connection_args
        optional_args = connection_args.setdefault("optional_args", {})
        if "port" in connection_args:  # valid port in connection_args overwrites invalid result in optional_args
            port = connection_args.pop("port")
            if not optional_args.get("port"):
                optional_args["port"] = port

        # convert the netmiko naming format to the native napalm format
        driver_lookup = {"arista_eos": "eos", "juniper": "junos", "cisco_xr": "iosxr", "nxos": "nxos",
                         "cisco_nxos_ssh": "nxos_ssh", "cisco_ios": "ios"}
        self.driver = driver_lookup[self.connection_args.get("device_type", False)]
        self.connection_args["hostname"] = self.connection_args.pop("host")
        del self.connection_args["device_type"]

    def connect(self):
        try:
            driver = napalm.get_network_driver(self.driver)
            napalmses = driver(**self.connection_args)
            return napalmses
        except Exception as e:
            write_meta_error(f"{e}")

    def sendcommand(self, session=False, command=False):
        try:
            result = {}
            session.open()
            for c in command:
                if hasattr(session, str(c)):
                    response = getattr(session, str(c))()
                    result[c] = response
                else:
                    response = session.cli([c])
                    result[c] = response[c].split("\n")
            return result
        except Exception as e:
            write_meta_error(f"{e}")

    def config(self, session=False, command=False, dry_run=False):
        try:
            if type(command) == list:
                napalmconfig = ""
                for comm in command:
                    napalmconfig += comm + "\n"
            else:
                napalmconfig = command
            session.open()
            session.load_merge_candidate(config=napalmconfig)
            diff = session.compare_config()
            if dry_run:
                response = session.discard_config()
            else:
                response = session.commit_config()
            result = {}
            result["changes"] = diff.split("\n")
            return result
        except Exception as e:
            write_meta_error(f"{e}")

    def logout(self, session):
        try:
            response = session.close()
            return response
        except Exception as e:
            write_meta_error(f"{e}")
