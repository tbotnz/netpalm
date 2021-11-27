from typing import List
from unittest.mock import Mock, MagicMock

from napalm.base.base import NetworkDriver
import pytest
from pytest_mock import MockerFixture

from netpalm.backend.core.utilities.rediz_meta import NetpalmMetaProcessedException
from netpalm.backend.plugins.drivers.napalm.napalm_drvr import naplm
from netpalm.backend.plugins.calls.getconfig.exec_command import exec_command

NAPALM_C_ARGS = {
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
def napalm_get_network_driver(mocker: MockerFixture) -> MockerFixture:
    get_network_driver = mocker.patch('netpalm.backend.plugins.drivers.napalm.napalm_drvr.napalm.get_network_driver',
                             autospec=True)
    mocked_driver = Mock()

    get_network_driver.return_value = mocked_driver
    get_network_driver.driver = mocked_driver  # for reference

    mocked_session = MagicMock(spec=NetworkDriver)  # otherwise hasatter(anything) is always True
    mocked_driver.return_value = mocked_session
    get_network_driver.session = mocked_session  # for reference


    def get_config():
        return ["my config"]

    def cli(commands: List):
        return {
            command: f"ran {command}"
            for command in commands
        }

    mocked_session.get_config.side_effect = get_config
    mocked_session.cli.side_effect = cli
    mocked_session.compare_config.return_value = "abc\nxyz"

    return get_network_driver


def test_napalm_connect(napalm_get_network_driver: Mock, rq_job):
    napalm_driver = naplm(kwarg={}, connection_args=NAPALM_C_ARGS.copy())
    assert napalm_driver.driver == "ios"
    sesh = napalm_driver.connect()
    napalm_get_network_driver.assert_called_with("ios")
    napalm_get_network_driver.driver.assert_called_once_with(hostname=NAPALM_C_ARGS["host"],
                                                             username=NAPALM_C_ARGS["username"],
                                                             password=NAPALM_C_ARGS["password"])


def test_napalm_sendcommand(napalm_get_network_driver: Mock, rq_job):
    napalm_driver = naplm(kwarg={}, connection_args=NAPALM_C_ARGS.copy())
    assert napalm_driver.driver == "ios"
    mock_session = napalm_driver.connect()
    assert napalm_get_network_driver.called  # make *certain* mock is used

    result = napalm_driver.sendcommand(mock_session, command=["get_config"])
    assert result["get_config"] == ["my config"]
    assert mock_session.open.called
    assert mock_session.get_config.called

    result = napalm_driver.sendcommand(mock_session, command=["show run"])
    assert result["show run"] == ["ran show run"]
    mock_session.cli.assert_called_with(["show run"])

    mock_session.get_config.reset_mock()
    mock_session.cli.reset_mock()
    result = napalm_driver.sendcommand(mock_session, command=["get_config", "show run"])
    assert result["get_config"] == ["my config"]
    assert result["show run"] == ["ran show run"]
    assert mock_session.get_config.called
    mock_session.cli.assert_called_with(["show run"])


def test_napalm_config(napalm_get_network_driver: Mock, rq_job):
    napalm_driver = naplm(kwarg={}, connection_args=NAPALM_C_ARGS.copy())
    assert napalm_driver.driver == "ios"
    mock_session = napalm_driver.connect()
    assert napalm_get_network_driver.called  # make *certain* mock is used

    _ = napalm_driver.config(mock_session, command=["get_config"])
    assert mock_session.open.called
    assert mock_session.load_merge_candidate.called
    assert mock_session.compare_config.called
    assert mock_session.commit_config.called
    assert not mock_session.discard_config.called

    mock_session.reset_mock()
    assert not mock_session.open.called
    _ = napalm_driver.config(mock_session, command=["get_config"], dry_run=True)
    assert mock_session.open.called
    assert mock_session.load_merge_candidate.called
    assert mock_session.compare_config.called
    assert not mock_session.commit_config.called
    assert mock_session.discard_config.called


def test_napalm_gc_exec_command(napalm_get_network_driver: Mock):
    ec_kwargs = {
        "library": "napalm",
        "command": ["get_config", "show run"],
        "connection_args": NAPALM_C_ARGS.copy()
    }
    mock_session = napalm_get_network_driver.session

    result = exec_command(**ec_kwargs)

    napalm_get_network_driver.assert_called_once_with("ios")
    napalm_get_network_driver.driver.assert_called_once_with(hostname=NAPALM_C_ARGS["host"],
                                                             username=NAPALM_C_ARGS["username"],
                                                             password=NAPALM_C_ARGS["password"])

    assert result["get_config"] == ["my config"]
    assert result["show run"] == ["ran show run"]
    assert napalm_get_network_driver.session.close.called


def test_napalm_gc_exec_command_post_checks(napalm_get_network_driver: Mock, rq_job):

    command, post_check_command = "get_config", "show run"

    good_post_check = {
        "get_config_args": {"command": post_check_command},
        "match_str": [post_check_command],
        "match_type": "include"
    }

    bad_post_check = {
        "get_config_args": {"command": post_check_command},
        "match_str": [post_check_command],
        "match_type": "exclude"
    }

    _ = exec_command(library="napalm", command=command,
                          connection_args=NAPALM_C_ARGS.copy(), post_checks=[good_post_check])

    napalm_get_network_driver.assert_called_once_with("ios")
    napalm_get_network_driver.driver.assert_called_once_with(hostname=NAPALM_C_ARGS["host"],
                                                             username=NAPALM_C_ARGS["username"],
                                                             password=NAPALM_C_ARGS["password"])

    with pytest.raises(NetpalmMetaProcessedException):
        _ = exec_command(library="napalm", command=command,
                         connection_args=NAPALM_C_ARGS.copy(), post_checks=[bad_post_check])
