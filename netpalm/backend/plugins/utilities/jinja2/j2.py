from jinja2 import Environment, FileSystemLoader
from jinja2schema import infer, to_json_schema

from netpalm.backend.core.confload.confload import config


class j2:

    def __init__(self, j2_type=False, **kwargs):
        self.kwarg = kwargs.get('kwargs', False)
        if j2_type == "config":
            self.jinja_template_dir = config.jinja2_config_templates
        if j2_type == "webhook":
            self.jinja_template_dir = config.webhook_jinja2_templates
        self.file_loader = FileSystemLoader(self.jinja_template_dir)
        self.env = Environment(loader=self.file_loader, lstrip_blocks=True, trim_blocks=True)

    def opentemplate(self, template):
        try:
            with open(template) as f:
                res = f.read()
                return str(res)
        except Exception as e:
            return e

    def gettemplate(self, template):
        try:
            templat = self.jinja_template_dir + template + '.j2'
            res = self.opentemplate(templat)
            try:
                schema = infer(res)
                js_schema = to_json_schema(schema)
            except Exception:
                js_schema = "error reading schema"
            resultdata = {
                    'status': 'success',
                    'data': {
                        "task_result": {
                            "template_schema": js_schema,
                            "template_data": res
                        }
                    }
            }
            return resultdata
        except Exception as e:
            resultdata = {
                    'status': 'error',
                    'data': str(e)
            }
            return resultdata

    def render_j2template(self, template, **kwargs):
        try:
            kwargs = kwargs.get("kwargs", False)
            templat = template + '.j2'
            tmp_template = self.env.get_template(templat)
            output = tmp_template.render(kwargs)
            resultdata = {
                    'status': 'success',
                    'data': {
                        "task_result": {
                            "template": template,
                            "template_render_result": str(output),
                        }
                    }
            }
            return resultdata
        except Exception as e:
            return e


def j2gettemplate(tmplate, template_type=False):
    t = j2(j2_type=template_type)
    res = t.gettemplate(tmplate)
    return res


def render_j2template(templat, template_type=False, **kwargs):
    t = j2(j2_type=template_type)
    res = t.render_j2template(template=templat, kwargs=kwargs["kwargs"])
    return res
