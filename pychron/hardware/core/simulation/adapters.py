from dataclasses import replace
from time import time

from .faults import FaultPolicy
from .protocols import SimulatorResponse
from .session import TransportEvent, TransportSession


class TransportAdapter:
    simulation = True

    def __init__(self, transport_kind="", fault_policy=None):
        self.transport_kind = transport_kind
        self.fault_policy = fault_policy or FaultPolicy()
        self.connected = False
        self._pending_reads = []
        self._last_response = None

    def open(self, **kw):
        self.connected = True
        return True

    def close(self):
        self.connected = False

    def reset(self):
        self.close()
        self.open()

    def write(self, payload, **kw):
        raise NotImplementedError

    def read(self, **kw):
        if self._pending_reads:
            return self._pending_reads.pop(0)

    def request(self, payload, **kw):
        raise NotImplementedError

    def readline(self, terminator=None, **kw):
        return self.read(terminator=terminator, **kw)

    def select_read(self, terminator=None, **kw):
        return self.read(terminator=terminator, **kw)


class ReplayTransportAdapter(TransportAdapter):
    def __init__(self, session, mode=None, fault_policy=None):
        super().__init__(
            transport_kind=session.transport_kind if session else "",
            fault_policy=fault_policy,
        )
        self.session = session or TransportSession(transport_kind="")
        self.mode = mode or self.session.mode or "strict"
        self._index = 0
        self._scripted_counts = {}

    def write(self, payload, **kw):
        event = self._match_event(payload)
        event = self._apply_faults("write", event)
        if event.response_payload is not None:
            self._pending_reads.append(event.response_payload)
        return payload

    def request(self, payload, **kw):
        event = self._match_event(payload)
        event = self._apply_faults("request", event)
        self._last_response = event.response_payload
        return event.response_payload

    def read(self, **kw):
        if self._pending_reads:
            payload = self._pending_reads.pop(0)
            event = TransportEvent(
                event_type="read",
                response_payload=payload,
                direction="read",
                timestamp=time(),
            )
            event = self._apply_faults("read", event)
            self._last_response = event.response_payload
            return event.response_payload

    def _match_event(self, payload):
        if self.mode == "scripted":
            matches = [
                event
                for event in self.session.events
                if event.request_payload == payload and event.event_type == "exchange"
            ]
            if not matches:
                raise AssertionError(f"no scripted replay event for {payload!r}")
            idx = self._scripted_counts.get(payload, 0)
            event = matches[min(idx, len(matches) - 1)]
            self._scripted_counts[payload] = idx + 1
            return replace(event)

        if self._index >= len(self.session.events):
            raise AssertionError(f"unexpected request {payload!r}; replay exhausted")

        event = replace(self.session.events[self._index])
        self._index += 1
        if event.request_payload != payload:
            raise AssertionError(
                f"replay mismatch expected {event.request_payload!r} got {payload!r}"
            )
        return event

    def _apply_faults(self, stage, event):
        context = {"adapter": self, "last_response": self._last_response}
        return self.fault_policy.apply(stage, event, context=context)


class RecordingTransportAdapter(TransportAdapter):
    def __init__(self, wrapped, session=None):
        super().__init__(transport_kind=getattr(wrapped, "transport_kind", ""))
        self.wrapped = wrapped
        self.session = session or TransportSession(transport_kind=self.transport_kind)

    def open(self, **kw):
        result = self.wrapped.open(**kw)
        self.connected = self.wrapped.connected
        self.session.append(
            TransportEvent(event_type="open", direction="lifecycle", timestamp=time())
        )
        return result

    def close(self):
        self.wrapped.close()
        self.connected = False
        self.session.append(
            TransportEvent(event_type="close", direction="lifecycle", timestamp=time())
        )

    def write(self, payload, **kw):
        result = self.wrapped.write(payload, **kw)
        self.session.append(
            TransportEvent(
                event_type="exchange",
                request_payload=payload,
                response_payload=None,
                timestamp=time(),
            )
        )
        return result

    def request(self, payload, **kw):
        response = self.wrapped.request(payload, **kw)
        self.session.append(
            TransportEvent(
                event_type="exchange",
                request_payload=payload,
                response_payload=response,
                timestamp=time(),
            )
        )
        return response

    def read(self, **kw):
        response = self.wrapped.read(**kw)
        self.session.append(
            TransportEvent(
                event_type="read",
                response_payload=response,
                direction="read",
                timestamp=time(),
            )
        )
        return response


class SimulatorTransportAdapter(TransportAdapter):
    def __init__(self, transport_kind, protocol, state=None, fault_policy=None):
        super().__init__(transport_kind=transport_kind, fault_policy=fault_policy)
        self.protocol = protocol
        self.state = state or {}

    def write(self, payload, **kw):
        response = self._handle(payload)
        if response.response is not None:
            self._pending_reads.append(response.response)
        self._pending_reads.extend(response.queued_reads)
        return payload

    def request(self, payload, **kw):
        response = self._handle(payload)
        self._pending_reads.extend(response.queued_reads)
        self._last_response = response.response
        return response.response

    def read(self, **kw):
        payload = super().read(**kw)
        if payload is None:
            return
        event = TransportEvent(
            event_type="read",
            response_payload=payload,
            direction="read",
            timestamp=time(),
        )
        event = self.fault_policy.apply(
            "read", event, state=self.state, context={"adapter": self, "last_response": self._last_response}
        )
        self._last_response = event.response_payload
        return event.response_payload

    def _handle(self, payload):
        event = TransportEvent(
            event_type="exchange",
            request_payload=payload,
            timestamp=time(),
        )
        response = self.protocol.handle(payload, self.state, context={"adapter": self})
        if not isinstance(response, SimulatorResponse):
            response = SimulatorResponse(response=response)
        event.response_payload = response.response
        event = self.fault_policy.apply(
            "request",
            event,
            state=self.state,
            context={"adapter": self, "last_response": self._last_response},
        )
        response.response = event.response_payload
        return response
