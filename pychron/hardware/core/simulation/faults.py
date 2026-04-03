class TransportTimeoutError(TimeoutError):
    pass


class TransportDisconnectError(ConnectionError):
    pass


class TransportMalformedPacketError(ValueError):
    pass


class FaultPolicy:
    def __init__(self, rules=None):
        self.rules = list(rules or [])
        self._counts = {}

    @classmethod
    def from_names(cls, names):
        return cls([{"fault": name} for name in names if name])

    def apply(self, stage, event, state=None, context=None):
        state = state or {}
        context = context or {}
        for idx, rule in enumerate(self.rules):
            if not self._matches(rule, stage, event):
                continue

            count = self._counts.get(idx, 0) + 1
            self._counts[idx] = count
            nth = rule.get("nth")
            if nth and count != nth:
                continue

            fault = rule["fault"]
            if fault == "timeout":
                raise TransportTimeoutError(rule.get("message", "simulated timeout"))
            if fault == "intermittent_disconnect":
                if context.get("adapter") is not None:
                    context["adapter"].connected = False
                raise TransportDisconnectError(
                    rule.get("message", "simulated disconnect")
                )
            if fault == "malformed_packet":
                payload = rule.get("response_payload", "<<MALFORMED>>")
                event.response_payload = payload
                continue
            if fault == "stale_status":
                last = context.get("last_response")
                if last is not None:
                    event.response_payload = last
                continue
            if fault == "out_of_range_values":
                event.response_payload = rule.get("response_payload", "999999")
                continue

        return event

    def _matches(self, rule, stage, event):
        rule_stage = rule.get("stage")
        if rule_stage and rule_stage != stage:
            return False

        match = rule.get("match")
        if match is None:
            return True

        request = event.request_payload
        if isinstance(request, bytes):
            try:
                request = request.decode("utf-8")
            except UnicodeDecodeError:
                request = repr(request)

        if rule.get("contains", True):
            return request is not None and match in request
        return request == match
