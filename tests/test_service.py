import pytest
import requests
import random
from tests.helper import netpalm_testhelper

helper = netpalm_testhelper()

@pytest.mark.service
def test_prepare_vlan_service_environment():
    pl = {
        "operation": "delete",
        "args":{
            "hosts":["10.0.2.25","10.0.2.23"],
            "username":"admin",
            "password":"admin"
        },
        "queue_strategy": "fifo"
    }
    reslist = helper.post_and_check('/service/vlan_service',pl)
    res = helper.check_many(reslist)
    if res:
        assert True
        
@pytest.mark.service
def test_create_vlan_service():
    pl = {
        "operation": "create",
        "args":{
            "hosts":["10.0.2.25","10.0.2.23"],
            "username":"admin",
            "password":"admin"
        },
        "queue_strategy": "fifo"
    }
    reslist = helper.post_and_check('/service/vlan_service',pl)
    res = helper.check_many(reslist)
    if "+int vlan 99" in res[0]["changes"][0] and "+int vlan 99" in res[1]["changes"][0]:
        assert True
    else:
        assert False

@pytest.mark.service
def test_retrieve_vlan_service():
    pl = {
        "operation": "retrieve",
        "args":{
            "hosts":["10.0.2.25","10.0.2.23"],
            "username":"admin",
            "password":"admin"
        },
        "queue_strategy": "fifo"
    }
    reslist = helper.post_and_check('/service/vlan_service',pl)
    res = helper.check_many(reslist)
    if res[0]["show int vlan 99"][0]["interface"] == "Vlan99" and res[1]["show int vlan 99"][0]["interface"] == "Vlan99":
        assert True
    else:
        assert False

@pytest.mark.service
def test_delete_vlan_service():
    pl = {
        "operation": "delete",
        "args":{
            "hosts":["10.0.2.25","10.0.2.23"],
            "username":"admin",
            "password":"admin"
        },
        "queue_strategy": "fifo"
    }
    reslist = helper.post_and_check('/service/vlan_service',pl)
    res = helper.check_many(reslist)
    if "-no int vlan 99" in res[0]["changes"][0] and "-no int vlan 99" in res[1]["changes"][0]:
        assert True
    else:
        assert False