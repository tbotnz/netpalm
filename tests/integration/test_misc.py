import pytest
import requests
from tests.integration.helper import NetpalmTestHelper

helper = NetpalmTestHelper()

@pytest.mark.misc_worker_router
def test_worker_route():
    """Workers endpoint was removed in Kafka migration — skip."""
    pytest.skip("Worker listing not applicable in Kafka architecture")
