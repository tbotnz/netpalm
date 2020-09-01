import pytest

from tests.helper import netpalm_testhelper

helper = netpalm_testhelper()


@pytest.mark.test_worker_route
def test_worker():
    res = helper.get('workers/')
    assert len(res) > 0


@pytest.mark.test_kill_worker
def test_kill_worker():
    resz = helper.get('workers/')
    rt = 'workers/kill/'+resz[0]["name"]
    rest = helper.post(rt)
    assert rest is None

