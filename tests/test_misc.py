import pytest
import requests
import json
from tests.helper import netpalm_testhelper

helper = netpalm_testhelper()

@pytest.mark.misc_worker_router
def test_worker_route():
    r = requests.get("http://"+helper.ip+":"+str(helper.port)+"/workers/", json={}, headers=helper.headers, timeout=helper.http_timeout)
    res = r.json()
    assert len(res) >= 2 

