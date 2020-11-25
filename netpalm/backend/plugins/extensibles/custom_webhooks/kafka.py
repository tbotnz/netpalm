import json
from kafka import KafkaProducer
import logging
from pprint import pprint

# from netpalm.backend.core.confload.confload import config

# this is a fairly simple example of a kafka producer webhook capability with netpalm

"""
netpalm webhook for posting a document directly to an kafka topic
IMPORTANT NOTES:
    webook requires a payload as per below
    "webhook": {
        "name": "wrm_kafka_producer_webhook",
        "args": {
            "topic": "test",
            "bootstrap_server": "kafka",        # hostname or IP of kafka broker
            "port": 29092                       # this is default if omitted,
            "message_format": json              # json - json is default if omitted. allow future options?
        }
    }
"""

log = logging.getLogger(__name__)

DEFAULT_KAFKA_PORT = 29092
DEFAULT_MESSAGE_FORMAT = "json"


def run_webhook(payload=False):
    try:
        if payload:
            log.info(f"run webhook: running kafka webhook")
            # set variables for Kafka
            topic = payload["webhook_args"]["topic"]
            bootstrap_server = payload["webhook_args"]["bootstrap_server"]
            kafka_port = payload["webhook_args"].get("port", DEFAULT_KAFKA_PORT)
            msg_format = payload["webhook_args"].get(
                "message_format", DEFAULT_MESSAGE_FORMAT
            )
            del payload["webhook_args"]

            print(f"DEBUG payload:  {payload}")

            data = payload.pop("data")
            task_result = data.pop("task_result")
            task_errors = data.pop("task_errors")

            # some debug output for testing
            print(f"DEBUG task_result:  {task_result}")
            print(f"DEBUG task_result:  {task_errors}")
            print()
            pprint(f"DEBUG data: {data}")

            # pull out certain fields into Kafka message headers as a list of tuples
            task_id = ("task_id", data.get("task_id").encode("utf-8"))
            created_on = ("created_on", data.get("created_on").encode("utf-8"))
            headers = [task_id, created_on]

            print(f"DEBUG headers:  {headers}")

            # NOTE: bootstrap_servers only supports single server at this time, could also be a list
            if msg_format.lower() == DEFAULT_MESSAGE_FORMAT:
                # json message format
                producer = KafkaProducer(
                    bootstrap_servers=f"{bootstrap_server}:{kafka_port}",
                    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                )
                print(f"DEBUG - task_result that will be sent to topic: {task_result}")
                producer.send(topic, task_result, headers=headers)

            else:
                # didn't specify a valid message format, raise ValueError
                raise ValueError("invalid message format specified")
            return True
        else:
            return False
    except Exception as e:
        log.error(f"Kafka webhook error: {e}")
        return e
