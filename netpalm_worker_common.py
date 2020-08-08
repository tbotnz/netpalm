import json
import logging.config
import typing
from multiprocessing.context import Process

from redis import Redis

from backend.core.confload.confload import config

log = logging.getLogger(__name__)


def handle_ping(**kwargs):
    #  Nothing to actually do here but dump to console
    log.info(f'GOT PING!')


def handle_broadcast_message(broadcast_msg: typing.Dict):
    try:
        msg_bytes = broadcast_msg['data']
        data = msg_bytes.decode()

    except (AttributeError, KeyError):
        log.error(f'Unintelligible broadcast message received (but this is normal '
                  f'at startup)!: {broadcast_msg}')
        return

    log.debug(f'got msg: {msg_bytes=}')

    try:
        data = json.loads(data)
    except json.JSONDecodeError:
        log.error(f'couldn\'t JSON decode message {data}')
        return

    handlers = {
        'ping': handle_ping,
    }
    msg_type = data['type']
    if msg_type not in handlers:
        log.error(f'received unimplemented broadcast message of type {msg_type}: {data}')
        return

    kwargs = data['kwargs']
    handlers[msg_type](**kwargs)


def broadcast_queue_worker(queue_name):
    try:
        redis = Redis(host=config.redis_server,
                      port=config.redis_port,
                      password=config.redis_key)
        pubsub = redis.pubsub()
        pubsub.subscribe(queue_name)

        log.info('Listening for broadcasts')
        for broadcast_msg in pubsub.listen():
            try:
                handle_broadcast_message(broadcast_msg)
            except Exception as e:
                log.exception('Error in broadcast queue handler')

    except Exception as e:
        log.exception('Error in broadcast queue')
        return e


def start_broadcast_listener_process():
    p = Process(target=broadcast_queue_worker, args=(config.redis_broadcast_q,))
    p.start()
