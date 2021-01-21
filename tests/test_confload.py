import os
from pathlib import Path
import pytest
pytestmark = pytest.mark.nolab

CONFIG_FILENAME = "config/config.json"
ACTUAL_CONFIG_PATH = Path(CONFIG_FILENAME).absolute()

if not ACTUAL_CONFIG_PATH.exists():
    ACTUAL_CONFIG_PATH = ACTUAL_CONFIG_PATH.parent.parent / CONFIG_FILENAME  # try ../config.json
    if not ACTUAL_CONFIG_PATH.exists():
        raise FileNotFoundError(f'Can\'t run confload tests without finding config.json, '
                                f'tried looking in {ACTUAL_CONFIG_PATH}')


os.environ["NETPALM_CONFIG"] = str(ACTUAL_CONFIG_PATH)
from netpalm.backend.core.confload import confload


def test_netpalm_config_honors_envvar():
    with pytest.raises(KeyError):
        config = confload.Config("DOES NOT EXIST.json")
        _ = config.data["__comment__"]

    with pytest.raises(KeyError):
        os.environ["NETPALM_CONFIG"] = "DOES NOT EXIST.JSON"
        config = confload.initialize_config()
        _ = config.data["__comment__"]

    # with pytest.raises(FileNotFoundError):  # this depends on the fact that you're running pytest from the tests directory
    #     del os.environ["NETPALM_CONFIG"]    # but we're not doing that anymore and it's okay really
    #     config = confload.initialize_config()

    config = confload.Config(ACTUAL_CONFIG_PATH)
    _ = config.data["__comment__"]
    os.environ["NETPALM_CONFIG"] = str(ACTUAL_CONFIG_PATH)
    config = confload.initialize_config()
    _ = config.data["__comment__"]


def test_netpalm_config_value_precedence(monkeypatch):
    file_config = confload.Config(ACTUAL_CONFIG_PATH)
    monkeypatch.setenv("NETPALM_REDIS_SERVER", "123.COM")
    envvar_config = confload.Config(ACTUAL_CONFIG_PATH)
    assert file_config.redis_key == envvar_config.redis_key
    assert envvar_config.redis_server == '123.COM'


def test_tfsm_search(monkeypatch):
    monkeypatch.setenv("NETPALM_TXTFSM_INDEX_FILE", "backend/plugins/extensibles/DOESNOTEXIT/index")
    config = confload.initialize_config(search_tfsm=False)
    config.setup_logging(max_debug=True)
    index_file_path = Path(config.txtfsm_index_file).absolute()
    assert not index_file_path.exists()

    config = confload.initialize_config()  # search_tfsm must default to True
    index_file_path = Path(config.txtfsm_index_file).absolute()
    assert index_file_path.exists()
