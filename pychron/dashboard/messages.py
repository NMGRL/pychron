import json
import pickle
import time


STRUCTURED_TOPIC = "dashboard"
HEARTBEAT_KIND = "heartbeat"
CONFIG_KIND = "config_snapshot"
VALUE_KIND = "value_update"
TIMEOUT_KIND = "timeout"
WARNING_KIND = "warning"
CRITICAL_KIND = "critical"
ERROR_KIND = "error"


def make_event(kind, **payload):
    payload["kind"] = kind
    payload["ts"] = payload.get("ts", time.time())
    return payload


def encode_event(event):
    return "{} {}".format(STRUCTURED_TOPIC, json.dumps(event, sort_keys=True))


def decode_event_message(message):
    if isinstance(message, bytes):
        message = message.decode("utf-8")

    prefix = "{} ".format(STRUCTURED_TOPIC)
    if not message.startswith(prefix):
        return None

    try:
        return json.loads(message[len(prefix) :])
    except (TypeError, ValueError):
        return None


def encode_config_payload(config):
    return json.dumps(make_event(CONFIG_KIND, config=config.as_payload())).encode("utf-8")


def decode_config_payload(payload):
    if isinstance(payload, bytes):
        payload = payload.decode("utf-8")
    event = json.loads(payload)
    if event.get("kind") != CONFIG_KIND:
        raise ValueError("Invalid dashboard config payload")
    return event["config"]


def encode_legacy_config_payload(values):
    return pickle.dumps(values)


def decode_legacy_config_payload(payload):
    return pickle.loads(payload)


def make_legacy_value_message(tag, value):
    return "{} {}".format(tag, value)


def make_legacy_error_message(message):
    return "error {}".format(message)


def parse_legacy_message(message):
    if isinstance(message, bytes):
        message = message.decode("utf-8")

    if message.startswith("error "):
        return make_event(ERROR_KIND, message=message.split("error ", 1)[1])

    if not message.startswith("<"):
        return None

    parts = message.split(" ", 1)
    if len(parts) != 2:
        return None

    tag, value = parts
    return make_event(VALUE_KIND, tag=tag, value=value)
