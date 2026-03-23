import pytest
import requests

from tests.integration.helper import NetpalmTestHelper

helper = NetpalmTestHelper()


@pytest.mark.test_worker_route
def test_worker():
    """Verify the API server is responsive."""
    url = f"{helper.base_url}/task/nonexistent"
    r = requests.get(url, headers=helper.headers, timeout=helper.http_timeout)
    # Should get a valid JSON response (not a connection error)
    assert r.status_code in (200, 404, 422)


@pytest.mark.test_kill_worker
def test_kill_worker():
    """Kill worker endpoint was removed in Kafka migration — skip."""
    pytest.skip("Worker kill not applicable in Kafka architecture")


@pytest.mark.test_pinned_container
def test_worker_pinned_container():
    """Pinned containers were removed in Kafka migration — verify pinned tasks still work."""
    pl = {
        "script": "hello_world",
        "args": {"hello": "world"},
        "queue_strategy": "pinned",
    }
    res = helper.post_and_check("/script", pl)
    assert res == "world"
