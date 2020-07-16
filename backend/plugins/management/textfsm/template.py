import json
from requests import get 
from backend.core.confload.confload import config
import shutil
import os

# syn
class template:

    def __init__(self, **kwargs):
        self.kwarg = kwargs.get('kwargs', False)
        self.indexfile = config().txtfsm_index_file
    
    def gettemplate(self):
        try:
            res = {}
            with open(self.indexfile, 'r', encoding='utf-8') as f:
                for line in f:
                    if "," in line and 'Template, Hostname, Platform, Command' not in line and not line.startswith('#'):
                        linearr = line.split(',')
                        drvr = linearr[2].replace(' ', '')
                        res[drvr] = []
            with open(self.indexfile, 'r', encoding='utf-8') as f:
                for line in f:                
                    if "," in line and 'Template, Hostname, Platform, Command' not in line and not line.startswith('#'):
                        linearr = line.split(',')
                        tmpfile = linearr[0]
                        comnd = linearr[3]
                        tmpobj = {"command":comnd, "template":tmpfile}
                        drvr = linearr[2].replace(' ', '')
                        res[drvr].append(tmpobj)
            resultdata = {
                    'status': 'success',
                    'data': {
                        "task_result": res
                    }
            }
            return resultdata
        except Exception as e:
            resultdata = {
                    'status': 'error',
                    'data': str(e)
            }
            return resultdata

    def addtemplate(self):
        try:
            #prepare args
            downloadf = self.kwarg["key"].split('_')[0]
            command = self.kwarg["command"].replace(' ','_')
            file_name = self.kwarg["driver"] + '_' + command + '.template'
            file_path = config().txtfsm_index_file.replace('index', '')
            fn = file_path + file_name

            #get and write
            with open(fn, "w") as file:
                response = get(config().txtfsm_template_server+'/static/fsms/'+downloadf+'.txt', timeout=10)
                file.write(response.text)

            #update index
            rewrite_data = []
            with open(self.indexfile, 'r+') as f: #r+ does the work of rw
                count = 0
                driver_line = False
                for line in f:
                    if line.startswith(self.kwarg["driver"]):
                        driver_line = True
                    elif not line.startswith(self.kwarg["driver"]) and driver_line and count == 0:
                        count +=1
                        rewrite_data.append(file_name+', .*,'+self.kwarg["driver"]+','+self.kwarg["command"]+'\n')
                    rewrite_data.append(line)
            tmpfile = config().txtfsm_index_file+'.tmp'
            with open(tmpfile, 'w') as f:
                for ln in rewrite_data:
                    f.write("%s" % ln)
            
            #reload indexfile
            shutil.move(tmpfile, config().txtfsm_index_file)
            resultdata = {
                    'status': 'success',
                    'data': {
                        "task_result": file_name + ' added'
                    }
            }
            return resultdata
        except Exception as e:
            resultdata = {
                    'status': 'error',
                    'data': str(e)
            }
            return resultdata

    def removetemplate(self):
        try:
            file_path = config().txtfsm_index_file.replace('index', '')
            fn = self.kwarg["template"]
            fl = file_path + fn
            os.remove(fl)

            #update index
            rewrite_data = []
            with open(self.indexfile, 'r+') as f: #r+ does the work of rw
                for line in f:
                    if not line.startswith(self.kwarg["template"]):
                        rewrite_data.append(line)

            tmpfile = config().txtfsm_index_file+'.tmp'
            with open(tmpfile, 'w') as f:
                for ln in rewrite_data:
                    f.write("%s" % ln)
            
            #reload indexfile
            shutil.move(tmpfile, config().txtfsm_index_file)
            resultdata = {
                    'status': 'success',
                    'data': {
                        "task_result": self.kwarg["template"] + ' removed'
                    }
            }
            return resultdata
        except Exception as e:
            resultdata = {
                    'status': 'error',
                    'data': str(e)
            }
            return resultdata        

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