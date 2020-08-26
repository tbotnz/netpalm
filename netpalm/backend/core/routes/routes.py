# load plugins
from netpalm.backend.plugins.calls.dryrun.dryrun import dryrun
from netpalm.backend.plugins.calls.getconfig.exec_command import exec_command
from netpalm.backend.plugins.calls.scriptrunner.script import script_exec
from netpalm.backend.plugins.calls.service.service import render_service
from netpalm.backend.plugins.calls.setconfig.exec_config import exec_config
from netpalm.backend.plugins.utilities.jinja2.j2 import j2gettemplate
from netpalm.backend.plugins.utilities.jinja2.j2 import render_j2template
from netpalm.backend.plugins.utilities.ls.ls import list_files
from netpalm.backend.plugins.utilities.textfsm.template import listtemplates, pushtemplate, addtemplate, removetemplate, \
    gettemplate

routes = {
    "getconfig": exec_command,
    "setconfig": exec_config,
    "listtemplates": listtemplates,
    "gettemplate": gettemplate,  # this is entirely unused now I think.
    "addtemplate": addtemplate,
    "pushtemplate": pushtemplate,
    "removetemplate": removetemplate,
    "ls": list_files,
    "script": script_exec,
    "j2gettemplate": j2gettemplate,
    "render_j2template": render_j2template,
    "render_service": render_service,
    "dryrun": dryrun
}
