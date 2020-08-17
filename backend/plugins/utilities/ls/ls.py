import logging
import os

from backend.core.confload.confload import config
from backend.core.models.task import ResponseBasic

log = logging.getLogger(__name__)


class ls:

    def __init__(self, folder=False):
        if folder == "config":
            self.folder_dir = config.jinja2_config_templates
            self.strip = ".j2"
        elif folder == "service":
            self.folder_dir = config.jinja2_service_templates
            self.strip = ".j2"
        elif folder == "webhook":
            self.folder_dir = config.webhook_jinja2_templates
            self.strip = ".j2"
        elif folder == "script":
            self.folder_dir = config.custom_scripts
            self.strip = ".py"

    def path_hierarchy(self, path, strip=False):
        try:
            files = []
            fileresult = []
            for r, d, f in os.walk(path):
                for file in f:
                    file.strip(path)
                    files.append(os.path.join(r, file))
            if len(files) > 0:
                for f in files:
                    if "__init__" not in f:
                        if "__pycache__" not in f:
                            if self.strip:
                                if self.strip in f:
                                    ftmpfile = f.replace(self.strip, '')
                                    fileresult.append(ftmpfile.replace(path, ''))
            resultdata = ResponseBasic(status="success", data={"task_result": {"templates": fileresult}}).dict()
            return resultdata
        except Exception as e:
            return str(e)

    def getfiles(self):
        try:
            res = self.path_hierarchy(path=self.folder_dir,strip=False)
            return res
        except Exception as e:
            return str(e)

    def bond_models(self):
        try:
            res = self.getfiles()
            return res
        except Exception as e:
            return str(e)

def list_files(fldr=False):
    res = ls(folder=fldr)
    response = res.getfiles()
    return response