import json
import logging.config
import typing
from multiprocessing.context import Process

from redis import Redis

from backend.core.confload.confload import config
from backend.plugins.utilities.textfsm.template import Template

log = logging.getLogger(__name__)


def handle_ping(**kwargs):
    #  Nothing to actually do here but dump to console
    log.info(f'GOT PING!')


def handle_add_template(**kwargs):
    log.debug(f'handle_add_template(): got {kwargs}')
    template = Template(kwargs=kwargs)
    result = template.addtemplate()
    status = result['status']
    if status == 'error':
        log.error(f'Failed to add template {template.kwarg} with error: {result["data"]}')
        return

    log.info(f'Result: {result["data"]}')


def handle_get_template(**kwargs):
    log.debug(f'handle_get_template(): got {kwargs}')
    template = Template(kwargs=kwargs)
    result = template.gettemplate()
    status = result['status']
    if status == 'error':
        log.error(f'Failed to get templates {template.kwarg} with error: {result["data"]}')
        return

    log.info(f'Result: {result["data"]}')


def handle_delete_template(**kwargs):
    log.debug(f'handle_delete_template(): got {kwargs}')
    template = Template(kwargs=kwargs)
    result = template.removetemplate()
    status = result['status']
    if status == 'error':
        log.error(f'Failed to delete template {template.kwarg} with error: {result["data"]}')
        return

    log.info(f'Result: {result["data"]}')


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
        'add_textfsm_template': handle_add_template,
        'get_textfsm_template': handle_get_template,
        'delete_textfsm_template': handle_delete_template
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
