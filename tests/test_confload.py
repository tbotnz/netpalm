import os
from pathlib import Path
import pytest
pytestmark = pytest.mark.nolab

CONFIG_FILENAME = "./config.json"
ACTUAL_CONFIG_PATH = Path(CONFIG_FILENAME).absolute()

if not ACTUAL_CONFIG_PATH.exists():
    ACTUAL_CONFIG_PATH = ACTUAL_CONFIG_PATH.parent.parent / CONFIG_FILENAME  # try ../config.json
    if not ACTUAL_CONFIG_PATH.exists():
        raise FileNotFoundError(f'Can\'t run confload tests without finding config.json, '
                                f'tried looking in {ACTUAL_CONFIG_PATH}')


os.environ["NETPALM_CONFIG"] = str(ACTUAL_CONFIG_PATH)
from backend.core.confload import confload


def test_netpalm_config_honors_envvar():
    with pytest.raises(FileNotFoundError):
        config = confload.Config("DOES NOT EXIST.json")

    with pytest.raises(FileNotFoundError):
        os.environ["NETPALM_CONFIG"] = "DOES NOT EXIST.JSON"
        config = confload.initialize_config()

    with pytest.raises(FileNotFoundError):  # this depends on the fact that you're running pytest from the tests directory
        del os.environ["NETPALM_CONFIG"]
        config = confload.initialize_config()

    config = confload.Config(ACTUAL_CONFIG_PATH)
    os.environ["NETPALM_CONFIG"] = str(ACTUAL_CONFIG_PATH)
    config = confload.initialize_config()


def test_netpalm_config_value_precedence(monkeypatch):
    file_config = confload.Config(ACTUAL_CONFIG_PATH)
    monkeypatch.setenv("NETPALM_REDIS_SERVER", "123.COM")
    envvar_config = confload.Config(ACTUAL_CONFIG_PATH)
    assert file_config.redis_key == envvar_config.redis_key
    assert envvar_config.redis_server == '123.COM'
