from unittest.mock import Mock

import pytest
from pytest_mock import MockerFixture

from netpalm.backend.plugins.drivers.netmiko.netmiko_drvr import netmko
from netpalm.backend.plugins.calls.getconfig.exec_command import exec_command

NETMIKO_COMMANDS = {
    "show run": """running config\na line\nanother line
    """,
    "show version": "ios v xyz",
    "show hostname": "wubba"
}

NETMIKO_C_ARGS = {
        "device_type": "cisco_ios",
        "host": "1.1.1.1",
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
def netmiko_connection_handler(mocker: MockerFixture) -> MockerFixture:
    mocked_CH = mocker.patch('netpalm.backend.plugins.drivers.netmiko.netmiko_drvr.ConnectHandler', autospec=True)

    mocked_session = Mock()

    mocked_CH.return_value = mocked_CH.session = mocked_session

    def mock_results(key, **kwargs):
        return NETMIKO_COMMANDS[key]
    mocked_session.send_command.side_effect = mock_results
    mocked_session.commit.return_value = "committed"
    mocked_session.save_config.return_value = "config saved"
    mocked_session.send_config_set.return_value = ""

    return mocked_CH


def test_netmko_connect(netmiko_connection_handler: Mock):
    netmiko_driver = netmko(kwarg={}, connection_args=NETMIKO_C_ARGS)
    sesh = netmiko_driver.connect()
    netmiko_connection_handler.assert_called_once_with(**NETMIKO_C_ARGS)


def test_netmko_sendcommand(netmiko_connection_handler: Mock):
    netmiko_driver = netmko(kwarg={}, connection_args={})
    sesh = netmiko_driver.connect()
    netmiko_connection_handler.assert_called()  # make *certain* mock is getting used

    result = netmiko_driver.sendcommand(sesh, NETMIKO_COMMANDS.keys())

    for command in NETMIKO_COMMANDS.keys():
        netmiko_connection_handler.session.send_command.assert_any_call(command)

    for command, value in NETMIKO_COMMANDS.items():
        assert result[command] == value.splitlines()


def test_netmko_config(netmiko_connection_handler: Mock, rq_job):
    netmiko_driver = netmko(kwarg={}, connection_args={})
    mock_session = netmiko_driver.connect()
    netmiko_connection_handler.assert_called()  # make *certain* mock is getting used

    _ = netmiko_driver.config(mock_session, "hostname asdf", dry_run=True, enter_enable=True)
    mock_session.send_config_set.assert_called_once_with(["hostname asdf"])
    assert not mock_session.commit.called
    assert mock_session.enable.called

    mock_session.commit.reset_mock()
    mock_session.enable.reset_mock()
    _ = netmiko_driver.config(mock_session, "hostname asdf")
    mock_session.send_config_set.assert_called_with(["hostname asdf"])
    assert mock_session.commit.called
    assert not mock_session.enable.called

    del mock_session.commit
    _ = netmiko_driver.config(mock_session, "hostname asdf")
    mock_session.send_config_set.assert_called_with(["hostname asdf"])
    assert mock_session.save_config.called


def test_netmiko_gc_exec_command(netmiko_connection_handler: Mock):
    ec_kwargs = {
        "library": "netmiko",
        "command": list(NETMIKO_COMMANDS.keys()),
        "connection_args": NETMIKO_C_ARGS
    }
    result = exec_command(**ec_kwargs)

    netmiko_connection_handler.assert_called_once_with(**NETMIKO_C_ARGS)
    for command, value in NETMIKO_COMMANDS.items():
        assert result[command] == value.splitlines()
    assert netmiko_connection_handler.session.disconnect.called


def test_netmiko_gc_exec_command_post_checks(netmiko_connection_handler: Mock, rq_job):
    netmiko_command_list = list(NETMIKO_COMMANDS.keys())

    command, post_check_command = netmiko_command_list[0], netmiko_command_list[-1]

    good_post_check = {
        "get_config_args": {"command": post_check_command},
        "match_str": ["wubba"],
        "match_type": "include"
    }

    bad_post_check = {
        "get_config_args": {"command": post_check_command},
        "match_str": ["wubba"],
        "match_type": "exclude"
    }

    result = exec_command(library="netmiko", command=command, connection_args=NETMIKO_C_ARGS, post_checks=[good_post_check])

    netmiko_connection_handler.assert_called_once_with(**NETMIKO_C_ARGS)
    for command, value in list(NETMIKO_COMMANDS.items())[:1]:
        assert result[command] == value.splitlines()

    with pytest.raises(Exception):
        result = exec_command(library="netmiko", command=command, connection_args=NETMIKO_C_ARGS, post_checks=[bad_post_check])


def test_netmiko_gc_exec_command_ttp(netmiko_connection_handler: Mock, rq_job):
    netmiko_command_list = list(NETMIKO_COMMANDS.keys())

    command = netmiko_command_list[0]

    netmiko_kwarg = {
        "ttp_template": "asdf"
    }
    result = exec_command(library="netmiko", command=command, connection_args=NETMIKO_C_ARGS, args=netmiko_kwarg.copy())

    with pytest.raises(AssertionError):
        netmiko_connection_handler.session.send_command.assert_called_once_with(command, **netmiko_kwarg)

    netmiko_kwarg["ttp_template"] = "netpalm/backend/plugins/extensibles/ttp_templates/asdf.ttp"
    netmiko_connection_handler.session.send_command.assert_called_once_with(command, **netmiko_kwarg)
