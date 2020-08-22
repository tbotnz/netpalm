from pprint import pprint

import pytest
import redis_lock

from backend.core.confload.confload import config

pytestmark = pytest.mark.nolab

from backend.core.confload import confload
from backend.core.redis import reds
from backend.core.redis.rediz import ExtnUpdateLog, ExtnUpdateLogType, ExtnUpdateLogEntry


@pytest.fixture(scope="function")
def clean_log():
    config = confload.initialize_config()
    extn_log = ExtnUpdateLog(reds.base_connection, config.redis_update_log, create=False)
    extn_log.clear()


def test_extensible_update_lock_behavior():
    lock = reds.extn_update_log.lock
    assert not lock.locked()

    with lock:  # should work
        assert lock.locked()
        with pytest.raises(redis_lock.AlreadyAcquired):
            with lock:  # should fail
                pass
        with pytest.raises(redis_lock.AlreadyAcquired):
            lock.acquire()

        new_lock = redis_lock.Lock(reds.base_connection, config.redis_update_log)
        assert not new_lock.acquire(blocking=False)


def test_extensible_update_log_creation(clean_log):
    extn_update_log = reds.extn_update_log
    assert not extn_update_log.exists
    extn_update_log.create()
    assert extn_update_log.exists

    new_log_obj = ExtnUpdateLog(reds.base_connection, reds.extn_update_log.log_name)
    assert new_log_obj.exists

    assert new_log_obj.get(-1).type is ExtnUpdateLogType.init


def test_extensible_update_log_add_fetch(clean_log):
    extn_update_log = reds.extn_update_log
    reds.extn_update_log.create(strict=True)

    item_1_dict = {
        "type": ExtnUpdateLogType.tfsm_pull,
        "data": {
            "key": "123_432",
            "driver": "dell_force10",
            "command": "show version"
        }
    }
    item_2_dict = {
        "type": ExtnUpdateLogType.tfsm_pull,
        "data": {
            "key": "999_876",
            "driver": "cisco_ios",
            "command": "show version"
        }
    }
    item_3_dict = {
        "type": ExtnUpdateLogType.init,
        "data": {
            "init": True
        }
    }
    item_dicts = [item_1_dict, item_2_dict, item_3_dict]
    items = [ExtnUpdateLogEntry(seq=index, **item_dict)
             for index, item_dict in enumerate(item_dicts, start=1)]

    pprint(items)

    with pytest.raises(ValueError):  # there can be only 1 init records are only valid at very start
        extn_update_log.add(items[-1])
    with pytest.raises(ValueError):
        extn_update_log.add(items[-1].dict())

    del item_dicts[2]
    del items[2]  # get rid of item_3

    assert (start_len := len(extn_update_log)) == 1  # should only have the init record now

    for item in items:
        extn_update_log.add(item)

    new_len = start_len + len(items)

    assert len(extn_update_log) == new_len

    with pytest.raises(IndexError):
        extn_update_log.get(new_len + 10)

    with pytest.raises(IndexError):
        _ = extn_update_log[new_len + 10]

    log_items = extn_update_log[1:]
    assert all(item == log_item for item, log_item in zip(items, log_items))

    for item in extn_update_log:
        print(item)  # proves the we can iterate over the log like a list
