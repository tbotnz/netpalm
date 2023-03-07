import json
import logging.config
import multiprocessing
import typing
from multiprocessing.context import Process

from netpalm.backend.core.confload.confload import config
from netpalm.backend.core.models.transaction_log import (
    TransactionLogEntryModel,
    TransactionLogEntryType,
)

from netpalm.backend.core.manager import ntplm, NetpalmManager
from netpalm.backend.core.utilities.rediz_kill_worker import kill_worker_pid
from netpalm.backend.core.utilities.rediz_worker_controller import RedisWorker

from netpalm.backend.core.utilities.textfsm.template import (
    listtemplates,
    addtemplate,
    removetemplate,
    pushtemplate,
)
from netpalm.backend.core.utilities.universal_template_mgr.unvrsl import unvrsl

log = logging.getLogger(__name__)
#
update_log_lock = multiprocessing.Lock()


class UpdateLogProcessor:
    def __init__(self, ntplm: NetpalmManager):  # quotes to avoid import issues
        self.lock = update_log_lock  # Purpose of this lock is to stop multiple processes (ex. gunicorn workers)
        # from processing the update log at once
        self.log = ntplm.extn_update_log
        self.last_seq_number = (
            -1
        )  # last sequence number handled.  -1 == not initialized

    def _get_lock(self):
        return self.lock.acquire(block=False)

    def _release_lock(self):
        return self.lock.release()

    def process_log(self, **kwargs):
        log.info("Processing update transaction log")
        rslt = 0
        with self.lock:
            log.info(f"Got lock for transaction log processing")
            new_entries = self.log[self.last_seq_number + 1 :]
            for entry in new_entries:
                self.process_entry(entry)
            rslt = len(new_entries)
        return rslt

    def process_entry(self, entry: TransactionLogEntryModel):
        if self.last_seq_number != entry.seq - 1:
            raise RuntimeError(
                f"Can't process {entry.seq} after {self.last_seq_number}!"
            )

        handlers = {
            TransactionLogEntryType.init: lambda **x: True,  # nothing to do
            TransactionLogEntryType.echo: handle_ping,
            TransactionLogEntryType.tfsm_pull: handle_add_template,
            TransactionLogEntryType.tfsm_delete: handle_delete_template,
            TransactionLogEntryType.tfsm_push: handle_push_template,
            TransactionLogEntryType.unvrsl_tmp_push: handle_push_universal_template,
            TransactionLogEntryType.unvrsl_tmp_delete: handle_delete_universal_template,
        }

        handler = handlers[entry.type]
        try:
            result = handler(**dict(entry.data))
        except KeyError:
            raise NotImplementedError(f"Can't handle {entry.type=}")
        self.last_seq_number = entry.seq
        return result


update_log_processor = UpdateLogProcessor(ntplm)


def handle_echo(msg: str):
    log.info(f"Echoing msg: {msg}")


def handle_ping(**kwargs):
    #  Nothing to actually do here but dump to console
    log.info("GOT PING!")


def handle_add_template(**kwargs):
    log.debug(f"handle_add_template(): got {kwargs}")
    result = addtemplate(**kwargs)
    status = result["status"]
    if status == "error":
        log.error(f"Failed to add template {kwargs} with error: {result['data']}")
        return

    log.info(f"Result: {result['data']}")


def handle_push_template(**kwargs):
    log.debug(f"handle_push_template(): got {kwargs}")
    result = pushtemplate(**kwargs)
    status = result["status"]
    if status == "error":
        log.error(f"Failed to push template {kwargs} with error: {result['data']}")
        return

    log.info(f"Result: {result['data']}")


def handle_get_template(**kwargs):
    log.debug(f"handle_get_template(): got {kwargs}")
    result = listtemplates(**kwargs)
    status = result["status"]
    if status == "error":
        log.error(f"Failed to get templates {kwargs} with error: {result['data']}")
        return

    log.info(f"Result: {len(str(result))} bytes of data")


def handle_delete_template(**kwargs):
    log.debug(f"handle_delete_template(): got {kwargs}")
    try:  # normalize key names
        fsm_template = kwargs.pop("fsm_template")
        kwargs["template"] = fsm_template
    except KeyError:
        pass

    result = removetemplate(**kwargs)
    status = result["status"]
    if status == "error":
        log.error(f"Failed to delete template {kwargs} with error: {result['data']}")
        return

    log.info(f'Result: {result["data"]}')


def handle_push_universal_template(**kwargs):
    log.debug(f"handle_push_universal_template(): got {kwargs}")
    template_mgr = unvrsl()
    result = template_mgr.add_template(payload=kwargs)
    status = result["status"]
    if status == "error":
        log.error(f"Failed to push template {kwargs} with error: {result['data']}")
        return
    log.info(f"Result: {result['data']}")


def handle_delete_universal_template(**kwargs):
    log.debug(f"handle_push_universal_template(): got {kwargs}")
    template_mgr = unvrsl()
    result = template_mgr.remove_template(payload=kwargs)
    status = result["status"]
    if status == "error":
        log.error(f"Failed to push template {kwargs} with error: {result['data']}")
        return
    log.info(f"Result: {result['data']}")


def handle_broadcast_message(broadcast_msg: typing.Dict):
    try:
        msg_bytes = broadcast_msg["data"]
        data = msg_bytes.decode()

    except (AttributeError, KeyError):
        log.error(
            f"Unintelligible broadcast message received (but this is normal "
            f"at startup)!: {broadcast_msg}"
        )
        return

    log.debug(f"got msg: {msg_bytes=}")

    try:
        data = json.loads(data)
    except json.JSONDecodeError:
        log.error(f"couldn't JSON decode message {data}")
        return

    handlers = {
        "ping": handle_ping,
        "process_update_log": update_log_processor.process_log,
        "kill_worker_pid": kill_worker_pid,
    }
    msg_type = data["type"]
    if msg_type not in handlers:
        log.error(
            f"received unimplemented broadcast message of type {msg_type}: {data}"
        )
        return

    kwargs = data["kwargs"]
    handlers[msg_type](**kwargs)


def broadcast_queue_worker(queue_name):
    try:
        log.info("Before listening for broadcasts, first check the log")
        update_log_processor.process_log()
        wr = RedisWorker(config)
        pubsub = wr.pub_sub()
        pubsub.subscribe(queue_name)

        log.info("Listening for broadcasts")
        for broadcast_msg in pubsub.listen():
            try:
                handle_broadcast_message(broadcast_msg)
            except Exception as e:
                log.exception(f"Error {e} in broadcast queue handler")

    except Exception as e:
        log.exception("Error in broadcast queue")
        return e


def start_broadcast_listener_process():
    p = Process(target=broadcast_queue_worker, args=(config.redis_broadcast_q,))
    p.start()
