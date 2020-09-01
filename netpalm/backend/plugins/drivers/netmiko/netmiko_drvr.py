import logging

from netmiko import ConnectHandler
from netmiko.cisco_base_connection import CiscoBaseConnection

from netpalm.backend.core.utilities.rediz_meta import write_meta_error

log = logging.getLogger(__name__)


class netmko:

    def __init__(self, **kwargs):
        self.kwarg = kwargs.get("args", False)
        self.connection_args = kwargs.get("connection_args", False)

    def connect(self):
        try:
            netmikoses = ConnectHandler(**self.connection_args)
            return netmikoses
        except Exception as e:
            write_meta_error(f"{e}")

    def sendcommand(self, session=False, command=False):
        try:
            result = {}
            for commands in command:
                if self.kwarg:
                    response = session.send_command(commands, **self.kwarg)
                    if response:
                        result[commands] = response
                else:
                    response = session.send_command(commands)
                    if response:
                        result[commands] = response.split("\n")
            return result
        except Exception as e:
            write_meta_error(f"{e}")

    def config(self, session: CiscoBaseConnection, command='', enter_enable=False):
        try:
            if type(command) == list:
                comm = command
            else:
                comm = command.splitlines()

            if enter_enable:
                session.enable()

            if self.kwarg:
                response = session.send_config_set(comm, **self.kwarg)
            else:
                response = session.send_config_set(comm)

            result = {}
            result["changes"] = response.split("\n")
            return result
        except Exception as e:
            write_meta_error(f"{e}")

    def logout(self, session):
        try:
            response = session.disconnect()
            return response
        except Exception as e:
            write_meta_error(f"{e}")
