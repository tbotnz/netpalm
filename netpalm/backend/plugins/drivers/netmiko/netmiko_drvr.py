import logging

from netmiko import ConnectHandler
from netmiko.cisco_base_connection import CiscoBaseConnection

from netpalm.backend.core.confload.confload import config
from netpalm.backend.core.utilities.rediz_meta import write_meta_error

log = logging.getLogger(__name__)


class netmko:
    def __init__(self, **kwargs):
        self.kwarg = kwargs.get("args", False)
        self.connection_args = kwargs.get("connection_args", False)
        #  support IOSXR commit labels
        self.commit_label = None
        if self.kwarg:
            if commit_label := self.kwarg.get("commit_label", None):
                self.commit_label = commit_label
                del self.kwarg["commit_label"]

    def connect(self):
        try:
            netmikoses = ConnectHandler(**self.connection_args)
            return netmikoses
        except Exception as e:
            write_meta_error(e)

    def sendcommand(self, session=False, command=False):
        try:
            result = {}
            for commands in command:
                if self.kwarg:
                    # normalise the ttp template name for ease of use
                    if "ttp_template" in self.kwarg.keys():
                        if self.kwarg["ttp_template"]:
                            template_name = config.ttp_templates + self.kwarg["ttp_template"] + ".ttp"
                            self.kwarg["ttp_template"] = template_name
                    response = session.send_command(commands, **self.kwarg)
                    if response:
                        result[commands] = response
                else:
                    response = session.send_command(commands)
                    if response:
                        result[commands] = response.split("\n")
            return result
        except Exception as e:
            write_meta_error(e)

    def config(self,
               session=False,
               command='',
               enter_enable=False,
               dry_run=False):
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

            if not dry_run:
                # CiscoBaseConnection(BaseConnection)
                # implements commit and save_config in child classes
                if hasattr(session, "commit") and callable(session.commit):
                    try:
                        if self.commit_label:
                            response += session.commit(label=self.commit_label)
                        else:
                            response += session.commit()
                    except AttributeError:
                        pass
                    except Exception as e:
                        write_meta_error(e)

                elif hasattr(session, "save_config") and callable(
                        session.save_config):
                    try:
                        response += session.save_config()
                    except AttributeError:
                        pass
                    except Exception as e:
                        write_meta_error(e)

            result = {}
            result["changes"] = response.split("\n")
            return result
        except Exception as e:
            write_meta_error(e)

    def logout(self, session):
        try:
            response = session.disconnect()
            return response
        except Exception as e:
            write_meta_error(e)
