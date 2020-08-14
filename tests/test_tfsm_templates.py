import os
import typing
from pathlib import Path
from pprint import pprint
from random import randint

import pytest

pytestmark = pytest.mark.nolab

from backend.core.confload import confload
from backend.plugins.utilities.textfsm.template import Template
from routers.route_utils import cacheable_model, http_error_handler, cache_key_from_req_data, poison_host_cache
from backend.core.models.models import model_getconfig
from backend.core.redis import rediz


def test_template_object():
    config = confload.initialize_config()
    template_obj = Template()
    result = template_obj.gettemplate()
    assert 'Errno' not in result.get('data', '')
    assert result['status'] != 'error'


# pull mapping of drivers to list of template mappings
def test_get_template_list():
    template_obj = Template()
    result = template_obj.gettemplate()
    assert 'task_result' in result['data']
    tr = result['data']['task_result']
    assert len(tr) > 0
    for driver, template_mappings in tr.items():
        assert isinstance(driver, str)
        assert isinstance(template_mappings, list)
        for template_mapping in template_mappings:
            assert 'command' in template_mapping
            assert 'template' in template_mapping
