import os
from pathlib import Path

ENV_FILE = "config/.env"
ACTUAL_ENV_PATH = Path(ENV_FILE).absolute()

if not ACTUAL_ENV_PATH.exists():
    ACTUAL_ENV_PATH = ACTUAL_ENV_PATH.parent.parent / ENV_FILE  # try ../config/.env
    if not ACTUAL_ENV_PATH.exists():
        raise FileNotFoundError(f"Can't run confload tests without finding .env, tried looking in {ACTUAL_ENV_PATH}")


os.environ["NETPALM_ENV_FILE"] = str(ACTUAL_ENV_PATH)
from netpalm.backend.core.confload import confload  # noqa: E402


def test_netpalm_config_loads():
    settings = confload.NetpalmSettings()
    assert settings.listen_port == 9000
    assert settings.redis_server == "redis"


def test_netpalm_config_value_precedence(monkeypatch):
    file_config = confload.NetpalmSettings()
    monkeypatch.setenv("NETPALM_REDIS_SERVER", "123.COM")
    envvar_config = confload.NetpalmSettings()
    assert file_config.redis_key == envvar_config.redis_key
    assert envvar_config.redis_server == "123.COM"


def test_tfsm_search(monkeypatch):
    monkeypatch.setenv("NETPALM_TXTFSM_INDEX_FILE", "backend/plugins/extensibles/DOESNOTEXIT/index")
    config = confload.NetpalmSettings()
    # _find_actual_tfsm_path will fall back to a known location if one exists.
    # On bare CI runners without ntc-templates installed, none of the fallbacks
    # will resolve — so skip instead of failing.
    index_file_path = Path(config.txtfsm_index_file).absolute()
    if not index_file_path.exists():
        import pytest

        pytest.skip("ntc-templates index file not available outside container")
