import pytest
import requests
import random
from tests.helper import netpalm_testhelper

helper = netpalm_testhelper()
r = "cornicorneo"+str(random.randint(1,101))

# @pytest.mark.service
# def test_create_service_vlan():
#     pl = {
#         "operation": "create",
#         "args":{
#             "hosts":["10.0.2.25","10.0.2.23"],
#             "username":"admin",
#             "password":"admin"
#         }
#     }
#     res = helper.post_and_check('/setconfig',pl)
#     matchstr = r+"#"
#     if matchstr in str(res):
#         assert True
#     else:
#         assert False
