import importlib
import inspect

import logging

from netpalm.backend.core.confload.confload import config
from netpalm.backend.core.utilities.rediz_meta import (
    render_netpalm_payload,
    write_mandatory_meta,
)
from netpalm.backend.core.utilities.rediz_meta import write_meta_error
from netpalm.backend.core.utilities.webhook.webhook import exec_webhook_func

from netpalm.backend.core.models.models import Script, ScriptCustom

from netpalm.backend.core.mongo.utils import write_task_result


log = logging.getLogger(__name__)


def script_model_finder(script_name: str):
    log.debug(f"script_model_finder: locating model for  {script_name}")
    model = Script
    model_defined = False
    model_mode = None
    # first check whether there is the legacy _model.py file against the script name
    try:
        model_name = f"{script_name}_model"
        template_model_path_raw = config.custom_scripts
        template_model_path = template_model_path_raw.replace("/", ".") + model_name
        module = importlib.import_module(template_model_path)
        model = getattr(module, model_name)
        model_defined = True
        model_mode = "legacy"
    except Exception as e:
        log.debug(
            f"script_model_finder: no legacy model found for {script_name} import error {e} attempting with newer model in file"
        )
        model = Script
        pass

    # if this does not exist, check within the file to see if a model exists
    # clean this up at some point -_-'

    try:
        model_name = f"{script_name}"
        template_model_path_raw = config.custom_scripts
        template_model_path = template_model_path_raw.replace("/", ".") + model_name
        module = importlib.import_module(template_model_path)
        runscrp = getattr(module, "run")
        for item in inspect.getfullargspec(runscrp):
            if type(item) is dict:
                for key, value in item.items():
                    if issubclass(value, ScriptCustom):
                        model = value
                        model_defined = True
                        model_mode = "new"
    except Exception as e:
        pass
    log.debug(f"script_model_finder: returning  {model}")
    return model, model_defined, model_mode


def script_kiddy(**kwargs):
    webhook = kwargs.get("webhook", False)
    result = False

    log.debug(f'script_kiddy: locating model for script {kwargs["script"]}')
    model = script_model_finder(kwargs["script"])
    model_to_validate = model[0]
    model_is_defined = model[1]
    model_mode = model[2]
    log.debug(
        f"script_kiddy: model located is {model} and a user model was found is {model_is_defined}"
    )

    try:
        write_mandatory_meta()

        # execute the script
        scrp_path = config.custom_scripts
        kwarg = kwargs
        arg = kwarg.get("args", False)
        script_name = kwarg.get("script", False)
        script_path_full_name = scrp_path.replace("/", ".") + script_name
        log.debug(
            f"script_kiddy: attempting to import script {script_path_full_name} for run"
        )

        module = importlib.import_module(script_path_full_name)
        runscrp = getattr(module, "run")
    except Exception as e:
        log.error(f"script_kiddy: could not import {script_path_full_name} with {e}")
        write_meta_error(e)

    try:
        log.debug(f"script_kiddy: attempting to run script {script_path_full_name}")
        if not model_is_defined or model_mode is "legacy":
            result = runscrp(kwargs=arg)
        else:
            data_to_send = model_to_validate(**kwarg)
            result = runscrp(data_to_send)
        # if webhook used do that too
        if webhook:
            current_jobdata = render_netpalm_payload(job_result=result)
            exec_webhook_func(jobdata=current_jobdata, webhook_payload=webhook)
    except Exception as e:
        log.error(
            f"script_kiddy: could not run script {script_path_full_name} with {e}"
        )
        write_meta_error(e)

    write_task_result(result_payload=result)
    return result
