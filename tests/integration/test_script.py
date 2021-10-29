import pytest
import requests
import random
from tests.integration.helper import NetpalmTestHelper

helper = NetpalmTestHelper()


@pytest.mark.script
def test_exec_script():
    pl = {"script": "hello_world", "args": {"hello": "world"}}
    res = helper.post_and_check("/script", pl)
    assert res == "world"


@pytest.mark.script
def test_exec_script_failure():
    pl = {"script": "hello_world", "args": {"bad": "args"}}
    res = helper.post_and_check("/script", pl)
    res2 = helper.post_and_check_errors("/script", pl)
    assert res is None
    assert res2 == ["Required args: 'hello'"]
