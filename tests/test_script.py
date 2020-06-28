import pytest
import requests
import random
from tests.helper import netpalm_testhelper

helper = netpalm_testhelper()

@pytest.mark.script
def test_exec_script():
    pl = {
        "script":"hello_world",
        "args":{
            "hello":"world"
        }
    }
    res = helper.post_and_check('/script',pl)
    assert res == "world"

