from pprint import pprint

import pytest
import redis_lock

from netpalm.backend.core.confload.confload import config

pytestmark = pytest.mark.nolab

from netpalm.backend.core.confload import confload
from netpalm.backend.core.redis import reds
from netpalm.backend.core.redis.rediz import ExtnUpdateLog, TransactionLogEntryType, TransactionLogEntryModel


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
            with lock:
                pass

        with pytest.raises(redis_lock.AlreadyAcquired):
            lock.acquire()

        new_lock = redis_lock.Lock(reds.base_connection, config.redis_update_log)
        assert not new_lock.acquire(blocking=False)  # proving 'acquire' fails with a new instance


def test_extensible_update_log_creation(clean_log):
    extn_update_log = reds.extn_update_log
    assert not extn_update_log.exists
    extn_update_log.create()
    assert extn_update_log.exists

    new_log_obj = ExtnUpdateLog(reds.base_connection, reds.extn_update_log.log_name)
    assert new_log_obj.exists

    assert new_log_obj.get(-1).type is TransactionLogEntryType.init


def test_extensible_update_log_add_fetch(clean_log):
    extn_update_log = reds.extn_update_log
    reds.extn_update_log.create(strict=True)

    item_1_dict = {
        "type": TransactionLogEntryType.tfsm_pull,
        "data": {
            "key": "123_432",
            "driver": "dell_force10",
            "command": "show version"
        }
    }
    item_2_dict = {
        "type": TransactionLogEntryType.tfsm_pull,
        "data": {
            "key": "999_876",
            "driver": "cisco_ios",
            "command": "show version"
        }
    }
    init_dict = {
        "type": TransactionLogEntryType.init,
        "data": {
            "init": True
        }
    }
    item_dicts = [item_1_dict, item_2_dict]
    items = [TransactionLogEntryModel(seq=index, **item_dict)
             for index, item_dict in enumerate(item_dicts, start=1)]

    pprint(items)

    with pytest.raises(ValueError):  # init records are only valid at very start
        extn_update_log.add(init_dict)

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


def test_update_log_processor(clean_log):
    from netpalm.netpalm_worker_common import UpdateLogProcessor, update_log_processor
    up = update_log_processor
    additional_up = UpdateLogProcessor(reds)

    echo_dict = {
        "type": TransactionLogEntryType.echo,
        "data": {
            "msg": "echo? ?   ECHO!!"
        }
    }
    assert up._get_lock()
    assert not additional_up._get_lock()
    up._release_lock()

    extn_update_log = reds.extn_update_log
    extn_update_log.create(strict=True)

    assert up.last_seq_number is -1

    assert up.process_log() == 1

    assert up.last_seq_number == 0

    for item in [echo_dict] * 3:
        extn_update_log.add(item)

    assert len(extn_update_log) == 4

    assert up.process_log() == 3
    assert up.last_seq_number == 3
