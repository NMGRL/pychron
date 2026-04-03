import base64
import json
from dataclasses import dataclass, field
from pathlib import Path


def _encode_payload(payload):
    if payload is None:
        return None
    if isinstance(payload, bytes):
        return {
            "encoding": "base64",
            "data": base64.b64encode(payload).decode("ascii"),
        }
    return {"encoding": "text", "data": payload}


def _decode_payload(payload):
    if payload is None:
        return None
    encoding = payload.get("encoding")
    data = payload.get("data")
    if encoding == "base64":
        return base64.b64decode(data.encode("ascii"))
    return data


@dataclass
class TransportEvent:
    event_type: str
    request_payload: object = None
    response_payload: object = None
    direction: str = "exchange"
    sequence: int = 0
    timestamp: float | None = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        return {
            "event_type": self.event_type,
            "request_payload": _encode_payload(self.request_payload),
            "response_payload": _encode_payload(self.response_payload),
            "direction": self.direction,
            "sequence": self.sequence,
            "timestamp": self.timestamp,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            event_type=data["event_type"],
            request_payload=_decode_payload(data.get("request_payload")),
            response_payload=_decode_payload(data.get("response_payload")),
            direction=data.get("direction", "exchange"),
            sequence=data.get("sequence", 0),
            timestamp=data.get("timestamp"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class TransportSession:
    transport_kind: str
    device_family: str = ""
    device_id: str = ""
    mode: str = "strict"
    tags: dict = field(default_factory=dict)
    events: list[TransportEvent] = field(default_factory=list)

    def append(self, event):
        event.sequence = len(self.events)
        self.events.append(event)
        return event

    def to_dict(self):
        return {
            "transport_kind": self.transport_kind,
            "device_family": self.device_family,
            "device_id": self.device_id,
            "mode": self.mode,
            "tags": dict(self.tags),
            "events": [event.to_dict() for event in self.events],
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            transport_kind=data.get("transport_kind", ""),
            device_family=data.get("device_family", ""),
            device_id=data.get("device_id", ""),
            mode=data.get("mode", "strict"),
            tags=data.get("tags", {}),
            events=[TransportEvent.from_dict(item) for item in data.get("events", ())],
        )

    def save(self, path):
        path = Path(path)
        path.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True))
        return path


def load_transport_session(path):
    path = Path(path)
    return TransportSession.from_dict(json.loads(path.read_text()))
