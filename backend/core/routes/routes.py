#load plugins
from backend.plugins.getconfig.exec_command import exec_command
from backend.plugins.setconfig.exec_config import exec_config
from backend.plugins.template.template import gettemplate
from backend.plugins.template.template import addtemplate
from backend.plugins.template.template import removetemplate

routes = {
    'getconfig':exec_command,
    'setconfig':exec_config,
    'gettemplate': gettemplate,
    'addtemplate': addtemplate,
    'removetemplate': removetemplate
    }
