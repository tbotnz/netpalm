import pytest
import requests
import random
from tests.integration.helper import NetpalmTestHelper

helper = NetpalmTestHelper()

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

