import logging

import importlib
import inspect

from typing import Any

from pydantic import BaseModel
from netpalm.backend.plugins.calls.service.netpalmservice import NetpalmService

from netpalm.backend.core.confload.confload import config

from netpalm.backend.core.utilities.rediz_meta import write_meta_error, write_mandatory_meta

log = logging.getLogger(__name__)


def get_service(service_name):
    log.debug(f"get_service: importing {service_name}")
    """ imports a service class and its model """
    model_name = f"{service_name}"
    return_obj = {"service_model": None, "service_class": None}
    template_model_path_raw = config.jinja2_service_templates
    template_model_path = template_model_path_raw.replace('/', '.') + model_name
    module = importlib.import_module(template_model_path)
    for name, obj in inspect.getmembers(module, inspect.isclass):
        if issubclass(obj, BaseModel):
            model = getattr(module, name)
            return_obj["service_model"] = model
        if issubclass(obj, NetpalmService):
            user_service = getattr(module, name)
            return_obj["service_class"] = user_service
    return return_obj


def create(**kwargs):
    log.debug(f"create: {kwargs}")
    write_mandatory_meta()
    try:
        service_name = kwargs["service_meta"]["service_model"]
        user_payload = kwargs["service_data"]
        service_lookup = get_service(service_name)
        svc = service_lookup["service_class"](service_lookup["service_model"], kwargs["service_meta"]["service_id"])
        log.debug(f"create: calling create on {service_name} with user data {user_payload}")
        res = svc.create(service_lookup["service_model"](**user_payload))
        return res
    except Exception as e:
        write_meta_error(f"create service: {kwargs} {e}")
        log.error(f"create: {kwargs} {e}")
        return e


def update(**kwargs):
    log.debug(f"update: {kwargs}")
    write_mandatory_meta()
    try:
        service_name = kwargs["service_meta"]["service_model"]
        user_payload = kwargs["service_data"]
        service_lookup = get_service(service_name)
        svc = service_lookup["service_class"](service_lookup["service_model"], kwargs["service_meta"]["service_id"])
        log.debug(f"update: calling update on {service_name} with user data {user_payload}")
        res = svc.update(service_lookup["service_model"](**user_payload))
        return res
    except Exception as e:
        write_meta_error(f"update service: {kwargs} {e}")
        log.error(f"update: {kwargs} {e}")
        return e


def delete(**kwargs):
    log.debug(f"update: {kwargs}")
    write_mandatory_meta()
    try:
        service_name = kwargs["service_meta"]["service_model"]
        user_payload = kwargs["service_data"]
        service_lookup = get_service(service_name)
        svc = service_lookup["service_class"](service_lookup["service_model"], kwargs["service_meta"]["service_id"])
        log.debug(f"delete: calling delete on {service_name} with user data {user_payload}")
        res = svc.delete(service_lookup["service_model"](**user_payload))
        return res
    except Exception as e:
        write_meta_error(f"delete service: {kwargs} {e}")
        log.error(f"delete: {kwargs} {e}")
        return e


def re_deploy(**kwargs):
    log.debug(f"re_deploy: {kwargs}")
    write_mandatory_meta()
    try:
        service_name = kwargs["service_meta"]["service_model"]
        user_payload = kwargs["service_data"]
        service_lookup = get_service(service_name)
        svc = service_lookup["service_class"](service_lookup["service_model"], kwargs["service_meta"]["service_id"])
        log.debug(f"re_deploy: calling re_deploy on {service_name} with user data {user_payload}")
        res = svc.re_deploy(service_lookup["service_model"](**user_payload))
        return res
    except Exception as e:
        write_meta_error(f"re_deploy service: {kwargs} {e}")
        log.error(f"re_deploy: {kwargs} {e}")
        return e


def validate(**kwargs):
    log.debug(f"validate: {kwargs}")
    write_mandatory_meta()
    try:
        service_name = kwargs["service_meta"]["service_model"]
        user_payload = kwargs["service_data"]
        service_lookup = get_service(service_name)
        svc = service_lookup["service_class"](service_lookup["service_model"], kwargs["service_meta"]["service_id"])
        log.debug(f"validate: calling validate on {service_name} with user data {user_payload}")
        res = svc.validate(service_lookup["service_model"](**user_payload))
        return res
    except Exception as e:
        write_meta_error(f"validate service: {kwargs} {e}")
        log.error(f"validate: {kwargs} {e}")
        return e


def health_check(**kwargs):
    log.debug(f"health_check: {kwargs}")
    write_mandatory_meta()
    try:
        service_name = kwargs["service_meta"]["service_model"]
        user_payload = kwargs["service_data"]
        service_lookup = get_service(service_name)
        svc = service_lookup["service_class"](service_lookup["service_model"], kwargs["service_meta"]["service_id"])
        log.debug(f"health_check: calling health_check on {service_name} with user data {user_payload}")
        res = svc.health_check(service_lookup["service_model"](**user_payload))
        return res
    except Exception as e:
        write_meta_error(f"health_check service: {kwargs} {e}")
        log.error(f"health_check: {kwargs} {e}")
        return e
