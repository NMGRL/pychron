from dataclasses import dataclass, field
from datetime import datetime, timedelta
import random


@dataclass
class SimulatorResponse:
    response: object = None
    queued_reads: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


class SimulatorProtocol:
    def handle(self, request, state, context=None):
        raise NotImplementedError


class NGXSimulatorProtocol(SimulatorProtocol):
    def __init__(self, seed=1):
        self._random = random.Random(seed)

    def handle(self, request, state, context=None):
        request = request.strip()
        state.setdefault("logged_in", False)
        state.setdefault("triggered", False)
        state.setdefault("valves", {})
        state.setdefault("source", {})
        state.setdefault("collection_time", datetime(2024, 1, 1, 12, 0, 0))
        state.setdefault("acq_count", 0)

        if request.startswith("Login "):
            state["logged_in"] = True
            return SimulatorResponse(response="E00")

        if request.startswith("SAB "):
            return SimulatorResponse(response="E00")

        if request.startswith("SetAcqPeriod "):
            return SimulatorResponse(response="E00")

        if request == "StopAcq":
            state["triggered"] = False
            return SimulatorResponse(response="E00")

        if request.startswith("StartAcq "):
            state["triggered"] = True
            state["acq_count"] += 1
            integration, rcs_id = request.split(" ", 1)[1].split(",", 1)
            state["collection_time"] += timedelta(seconds=max(1, int(integration)))
            ct = state["collection_time"].strftime("%H:%M:%S.%f")[:-3]
            base = float(state["acq_count"])
            signals = [
                f"{base + self._random.uniform(0.01, 0.05):0.5f}",
                f"{base + self._random.uniform(0.06, 0.10):0.5f}",
                f"{base + self._random.uniform(0.11, 0.15):0.5f}",
            ]
            line = "#EVENT:ACQ,{},SIM,SIM,{},{}#\r\n".format(
                rcs_id, ct, ",".join(signals)
            )
            return SimulatorResponse(response="E00", queued_reads=[line])

        if request.startswith("OpenValve "):
            addr = request.split(" ", 1)[1]
            state["valves"][addr] = True
            return SimulatorResponse(response="E00")

        if request.startswith("CloseValve "):
            addr = request.split(" ", 1)[1]
            state["valves"][addr] = False
            return SimulatorResponse(response="E00")

        if request.startswith("GetValveStatus "):
            addr = request.split(" ", 1)[1]
            return SimulatorResponse(
                response="OPEN" if state["valves"].get(addr, False) else "CLOSED"
            )

        if request.startswith("SetSourceOutput "):
            key, value = request.split(" ", 1)[1].split(",", 1)
            state["source"][key] = value
            return SimulatorResponse(response="E00")

        if request.startswith("GetSourceOutput "):
            key = request.split(" ", 1)[1]
            return SimulatorResponse(response=str(state["source"].get(key, "0.0")))

        return SimulatorResponse(response="E00")


class PychronValveSimulatorProtocol(SimulatorProtocol):
    def handle(self, request, state, context=None):
        request = request.strip()
        state.setdefault("valves", {})
        state.setdefault("locks", {})

        if " " in request:
            command, argument = request.split(" ", 1)
        else:
            command, argument = request, ""

        if command == "Open":
            state["valves"][argument] = True
            return SimulatorResponse(response="True")
        if command == "Close":
            state["valves"][argument] = False
            return SimulatorResponse(response="True")
        if command in ("GetValveState", "GetIndicatorState"):
            return SimulatorResponse(
                response="True" if state["valves"].get(argument, False) else "False"
            )
        if command == "GetValveLockState":
            return SimulatorResponse(
                response="True" if state["locks"].get(argument, False) else "False"
            )
        if command == "GetValveStates":
            parts = []
            for key in sorted(state["valves"]):
                parts.extend((key, "1" if state["valves"][key] else "0"))
            return SimulatorResponse(response=",".join(parts))
        if command == "GetValveLockStates":
            parts = []
            for key in sorted(state["locks"]):
                parts.extend((key, "1" if state["locks"][key] else "0"))
            return SimulatorResponse(response=",".join(parts))
        if command == "GetStateChecksum":
            return SimulatorResponse(response=str(len(state["valves"])))
        if command == "GetValveOwners":
            return SimulatorResponse(response="")
        return SimulatorResponse(response="")
