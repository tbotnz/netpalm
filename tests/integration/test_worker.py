import pytest

from tests.integration.helper import NetpalmTestHelper

helper = NetpalmTestHelper()


@pytest.mark.test_worker_route
def test_worker():
    res = helper.get("workers/")
    assert len(res) > 0


@pytest.mark.test_kill_worker
def test_kill_worker():
    resz = helper.get("workers/")
    rt = "workers/kill/" + resz[0]["name"]
    rest = helper.post(rt)
    assert rest is None


@pytest.mark.test_pinned_container
def test_worker_pinned_container():
    res = helper.get("containers/pinned/")
    assert len(res) > 0
