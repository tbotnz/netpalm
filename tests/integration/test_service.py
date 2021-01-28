import pytest
import requests
import random
import logging

from tests.integration.helper import NetpalmTestHelper

log = logging.getLogger(__name__)

helper = NetpalmTestHelper()

@pytest.mark.service
def test_prepare_vlan_service_environment():
    pl = {
        "operation": "create",
        "args": {
            "hosts": ["10.0.2.25", "10.0.2.23"],
            "username": "admin",
            "password": "admin"
        },
        "queue_strategy": "fifo"
    }
    reslist = helper.post_and_check('/service/vlan_service',pl)
    res = helper.check_many(reslist)
    if res:
        assert True
        
@pytest.mark.service
def test_create_vlan_service_instance():
    pl = {
        "operation": "create",
        "args": {
            "hosts": ["10.0.2.25", "10.0.2.23"],
            "username": "admin",
            "password": "admin"
        },
        "queue_strategy": "fifo"
    }
    reslist = helper.post_and_check('/service/vlan_service',pl)
    res = helper.check_many(reslist)
    if "(config)#int vlan 99" in res[0]["changes"][2] and "(config)#int vlan 99" in res[1]["changes"][2]:
        assert True
    else:
        assert False

@pytest.mark.fulllab
@pytest.mark.service
def test_retrieve_vlan_service():
    pl = {
        "operation": "retrieve",
        "args": {
            "hosts": ["10.0.2.25","10.0.2.23"],
            "username": "admin",
            "password": "admin"
        },
        "queue_strategy": "fifo"
    }
    reslist = helper.post_and_check('/service/vlan_service',pl)
    res = helper.check_many(reslist)
    if res[0]["show int vlan 99"][0]["interface"] == "Vlan99" and res[1]["show int vlan 99"][0]["interface"] == "Vlan99":
        assert True
    else:
        assert False

@pytest.mark.fulllab
@pytest.mark.service
def test_delete_vlan_service_legacy():
    pl = {
        "operation": "delete",
        "args": {
            "hosts": ["10.0.2.25","10.0.2.23"],
            "username": "admin",
            "password": "admin"
        },
        "queue_strategy": "fifo"
    }
    reslist = helper.post_and_check('/service/vlan_service',pl)
    res = helper.check_many(reslist)
    if "(config)#no int vlan 99" in res[0]["changes"][2] and "(config)#no int vlan 99" in res[1]["changes"][2]:
        assert True
    else:
        assert False

@pytest.mark.service
def test_create_vlan_service_instance():
    pl = {
        "operation": "create",
        "args": {
            "hosts": ["10.0.2.25", "10.0.2.23"],
            "username": "admin",
            "password": "admin"
        },
        "queue_strategy": "fifo"
    }
    reslist = helper.post('service/vlan_service', pl)
    assert reslist["data"]["service_id"]

@pytest.mark.service
def test_retrieve_vlan_service_instance():
    pl = {
        "operation": "create",
        "args": {
            "hosts": ["10.0.2.25", "10.0.2.23"],
            "username": "admin",
            "password": "admin"
        },
        "queue_strategy": "fifo"
    }
    q = helper.post('service/vlan_service', pl)
    # finish off at some point
    assert True