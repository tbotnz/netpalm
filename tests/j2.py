from backend.core.confload.confload import config
import os

from jinja2 import Template

# syn
class j2:

    def __init__(self, **kwargs):
        self.kwarg = kwargs.get('kwargs', False)
        self.jinja_template_dir = config().jinja2_templates

    def path_hierarchy(self, path):
        try:
            files = []
            fileresult = []
            for r, d, f in os.walk(path):
                for file in f:
                    file.strip(path)
                    files.append(os.path.join(r, file))
            if len(files) > 0:
                for f in files:
                    fileresult.append(f.replace(path, ''))
            return fileresult
        except Exception as e:
            raise ("error getting file path_hierarchy")

    def gettemplates(self):
        try:
            res = self.path_hierarchy(self.jinja_template_dir)
            return res
        except Exception as e:
            resultdata = {
                    'status': 'error',
                    'data': str(e)
            }
            return resultdata

    # def addtemplate(self):
    #     try:
    #         #reload indexfile
    #         shutil.move(tmpfile, config().txtfsm_index_file)
    #         resultdata = {
    #                 'status': 'success',
    #                 'data': {
    #                     "task_result": file_name + ' added'
    #                 }
    #         }
    #         return resultdata
    #     except Exception as e:
    #         resultdata = {
    #                 'status': 'error',
    #                 'data': str(e)
    #         }
    #         return resultdata

    # def removetemplate(self):
    #     try:

    #         shutil.move(tmpfile, config().txtfsm_index_file)
    #         resultdata = {
    #                 'status': 'success',
    #                 'data': {
    #                     "task_result": self.kwarg["template"] + ' removed'
    #                 }
    #         }
    #         return resultdata
    #     except Exception as e:
    #         resultdata = {
    #                 'status': 'error',
    #                 'data': str(e)
    #         }
    #         return resultdata        

def gettemplate():
    t = template()
    res = t.gettemplate()
    return res

def addtemplate(**kwargs):
    t = template(kwargs=kwargs["kwargs"])
    res = t.addtemplate()
    return res

def removetemplate(**kwargs):
    t = template(kwargs=kwargs["kwargs"])
    res = t.removetemplate()
    return res