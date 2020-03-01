#load plugins
from backend.plugins.getconfig.exec_command import exec_command
from backend.plugins.setconfig.exec_config import exec_config

routes = {
    'getconfig':exec_command,
    'setconfig':exec_config
    }
