# load plugins
from backend.plugins.calls.dryrun.dryrun import dryrun
from backend.plugins.calls.getconfig.exec_command import exec_command
from backend.plugins.calls.scriptrunner.script import script_exec
from backend.plugins.calls.service.service import render_service
from backend.plugins.calls.setconfig.exec_config import exec_config
from backend.plugins.utilities.jinja2.j2 import j2gettemplate
from backend.plugins.utilities.jinja2.j2 import render_j2template
from backend.plugins.utilities.ls.ls import list_files
from backend.plugins.utilities.textfsm.template import listtemplates, pushtemplate, addtemplate, removetemplate, \
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
