from typing import List
from unittest.mock import Mock, MagicMock

from napalm.base.base import NetworkDriver
import pytest
from pytest_mock import MockerFixture

from netpalm.backend.plugins.drivers.ncclient.ncclient_drvr import ncclien
from netpalm.backend.plugins.calls.getconfig.exec_command import exec_command

NCCLIENT_C_ARGS = {
        "device_type": "cisco_ios",
        "host": "1.1.1.1",
        "port": 830,
        "hostkey_verify": False,
        "username": "admin",
        "password": "admin"
    }


@pytest.fixture()
def rq_job(mocker: MockerFixture) -> MockerFixture:
    mocked_get_current_job = mocker.patch('netpalm.backend.core.utilities.rediz_meta.get_current_job')
    mocked_job = Mock()
    mocked_job.meta = {"errors": []}
    mocked_get_current_job.return_value = mocked_job


@pytest.fixture()
def xml_parse(mocker: MockerFixture) -> MockerFixture:
    mocked_xmlparser = mocker.patch('xmltodict.parse')
    return mocked_xmlparser


@pytest.fixture()
def ncclient_manager(mocker: MockerFixture) -> MockerFixture:
    manager = mocker.patch("netpalm.backend.plugins.drivers.ncclient.ncclient_drvr.manager")
    mocked_session = Mock()
    manager.connect.return_value = mocked_session
    manager.mocked_session = mocked_session
    return manager


def test_ncclient_connect(ncclient_manager: Mock, rq_job):
    c_arg_copy = NCCLIENT_C_ARGS.copy()
    ncclient_driver = ncclien(kwarg={}, connection_args=c_arg_copy)
    sesh = ncclient_driver.connect()
    assert sesh is ncclient_manager.mocked_session
    ncclient_manager.connect.assert_called_with(**c_arg_copy)


def test_ncclient_getmethod_empty_args(ncclient_manager: Mock, rq_job):
    c_arg_copy = NCCLIENT_C_ARGS.copy()
    ncclient_driver = ncclien(connection_args=c_arg_copy)
    sesh = ncclient_driver.connect()
    with pytest.raises(Exception):
        result = ncclient_driver.getmethod(sesh)


def test_ncclient_getmethod(ncclient_manager: Mock, rq_job):
    c_arg_copy = NCCLIENT_C_ARGS.copy()
    args = {
        "source": "running",
        "filter": "<filter type='subtree'>"
                    "<System xmlns='http://cisco.com/ns/yang/cisco-nx-os-device'></System>"
                  "</filter>",
    }
    ncclient_driver = ncclien(args=args, connection_args=c_arg_copy)
    sesh = ncclient_driver.connect()
    result = ncclient_driver.getmethod(sesh)
    sesh.get.assert_called_with(**args)
    assert result["get_config"] is sesh.get().data_xml


def test_ncclient_getmethod_rjson(ncclient_manager: Mock, rq_job, xml_parse):
    c_arg_copy = NCCLIENT_C_ARGS.copy()
    args = {
        "source": "running",
        "filter": "<filter type='subtree'>"
                    "<System xmlns='http://cisco.com/ns/yang/cisco-nx-os-device'></System>"
                  "</filter>",
        "render_json": True
    }
    ncclient_driver = ncclien(args=args.copy(), connection_args=c_arg_copy)
    sesh = ncclient_driver.connect()
    result = ncclient_driver.getmethod(sesh)
    sesh.get.assert_called_with(source=args["source"], filter=args["filter"])  # excluding render_json
    assert "get_config" in result
    assert isinstance(result["get_config"], Mock)
    assert result["get_config"] is xml_parse()


def test_ncclient_getconfig(ncclient_manager: Mock, rq_job):
    c_arg_copy = NCCLIENT_C_ARGS.copy()
    args = {
        "source": "running",
        "filter": "<filter type='subtree'>"
                    "<System xmlns='http://cisco.com/ns/yang/cisco-nx-os-device'></System>"
                  "</filter>",
    }
    ncclient_driver = ncclien(args=args, connection_args=c_arg_copy)
    sesh = ncclient_driver.connect()
    result = ncclient_driver.getconfig(sesh)
    sesh.get_config.assert_called_with(**args)
    assert result["get_config"] is sesh.get_config().data_xml


def test_ncclient_getconfig_rjson(ncclient_manager: Mock, rq_job, xml_parse):
    c_arg_copy = NCCLIENT_C_ARGS.copy()
    args = {
        "source": "running",
        "filter": "<filter type='subtree'>"
                    "<System xmlns='http://cisco.com/ns/yang/cisco-nx-os-device'></System>"
                  "</filter>",
        "render_json": True
    }
    ncclient_driver = ncclien(args=args.copy(), connection_args=c_arg_copy)
    sesh = ncclient_driver.connect()
    result = ncclient_driver.getconfig(sesh)
    sesh.get_config.assert_called_with(source=args["source"], filter=args["filter"])  # excluding render_json
    assert result["get_config"] is xml_parse()


def test_ncclient_getconfig_rpc(ncclient_manager: Mock, rq_job):
    c_arg_copy = NCCLIENT_C_ARGS.copy()
    args = {
        "source": "running",
        "filter": "<filter type='subtree'>"
                    "<System xmlns='http://cisco.com/ns/yang/cisco-nx-os-device'></System>"
                  "</filter>",
        "rpc": True
    }
    ncclient_driver = ncclien(args=args.copy(), connection_args=c_arg_copy)
    sesh = ncclient_driver.connect()
    result = ncclient_driver.getconfig(sesh)
    sesh.rpc.assert_called_with(**args)
    assert result["get_config"] is sesh.rpc().data_xml


def test_ncclient_getconfig_rpc_rjson(ncclient_manager: Mock, rq_job, xml_parse):
    c_arg_copy = NCCLIENT_C_ARGS.copy()
    args = {
        "source": "running",
        "filter": "<filter type='subtree'>"
                    "<System xmlns='http://cisco.com/ns/yang/cisco-nx-os-device'></System>"
                  "</filter>",
        "rpc": True,
        "render_json": True
    }
    ncclient_driver = ncclien(args=args.copy(), connection_args=c_arg_copy)
    sesh = ncclient_driver.connect()
    result = ncclient_driver.getconfig(sesh)
    sesh.rpc.assert_called_with(source=args["source"], filter=args["filter"], rpc=True)  # excluding render_json
    assert result["get_config"] is xml_parse()


def test_ncclient_editconfig(ncclient_manager: Mock, rq_job):
    c_arg_copy = NCCLIENT_C_ARGS.copy()
    args = {
        "source": "running",
        "filter": "<filter type='subtree'>"
                    "<System xmlns='http://cisco.com/ns/yang/cisco-nx-os-device'></System>"
                  "</filter>",
    }
    ncclient_driver = ncclien(args=args, connection_args=c_arg_copy)
    sesh = ncclient_driver.connect()
    result = ncclient_driver.editconfig(sesh)
    sesh.edit_config.assert_called_with(**args)
    assert result["edit_config"] is sesh.edit_config().xml
    assert sesh.commit.called
    assert not sesh.discard_changes.called


def test_ncclient_editconfig_rjson(ncclient_manager: Mock, rq_job, xml_parse):
    c_arg_copy = NCCLIENT_C_ARGS.copy()
    args = {
        "source": "running",
        "filter": "<filter type='subtree'>"
                    "<System xmlns='http://cisco.com/ns/yang/cisco-nx-os-device'></System>"
                  "</filter>",
        "render_json": True
    }
    ncclient_driver = ncclien(args=args.copy(), connection_args=c_arg_copy)
    sesh = ncclient_driver.connect()
    result = ncclient_driver.editconfig(sesh)
    sesh.edit_config.assert_called_with(source=args["source"], filter=args["filter"])  # excluding render_json
    assert result["edit_config"] is xml_parse()


def test_ncclient_editconfig_dry_run(ncclient_manager: Mock, rq_job):
    c_arg_copy = NCCLIENT_C_ARGS.copy()
    args = {
        "source": "running",
        "filter": "<filter type='subtree'>"
                    "<System xmlns='http://cisco.com/ns/yang/cisco-nx-os-device'></System>"
                  "</filter>",
    }
    ncclient_driver = ncclien(args=args, connection_args=c_arg_copy)
    sesh = ncclient_driver.connect()
    result = ncclient_driver.editconfig(sesh, dry_run=True)
    sesh.edit_config.assert_called_with(**args)
    assert result["edit_config"] is sesh.edit_config().xml
    assert not sesh.commit.called
    assert sesh.discard_changes.called


def test_ncclient_gc_exec_command(ncclient_manager: Mock, rq_job):
    args = {
        "source": "running",
        "filter": "<filter type='subtree'>"
                    "<System xmlns='http://cisco.com/ns/yang/cisco-nx-os-device'></System>"
                  "</filter>",
    }
    ec_kwargs = {
        "library": "ncclient",
        "connection_args": NCCLIENT_C_ARGS.copy(),
        "args": args
    }
    mocked_session = ncclient_manager.mocked_session

    result = exec_command(**ec_kwargs)

    mocked_session.get_config.assert_called_once_with(**args)

    assert result["get_config"] == mocked_session.get_config().data_xml
    assert mocked_session.close_session.called
