#load plugins
from backend.plugins.calls.getconfig.exec_command import exec_command
from backend.plugins.calls.setconfig.exec_config import exec_config
from backend.plugins.calls.service.service import render_service
from backend.plugins.calls.dryrun.dryrun import dryrun
from backend.plugins.calls.scriptrunner.script import script_exec

from backend.plugins.utilities.textfsm.template import gettemplate
from backend.plugins.utilities.textfsm.template import addtemplate
from backend.plugins.utilities.textfsm.template import removetemplate
from backend.plugins.utilities.jinja2.j2 import j2gettemplates
from backend.plugins.utilities.jinja2.j2 import j2gettemplate
from backend.plugins.utilities.jinja2.j2 import render_j2template


routes = {
    "getconfig":exec_command,
    "setconfig":exec_config,
    "gettemplate": gettemplate,
    "addtemplate": addtemplate,
    "removetemplate": removetemplate,
    "script": script_exec,
    "j2gettemplates": j2gettemplates,
    "j2gettemplate":j2gettemplate,
    "render_j2template":render_j2template,
    "render_service":render_service,
    "dryrun":dryrun
    }
