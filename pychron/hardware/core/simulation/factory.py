from pathlib import Path

from .adapters import ReplayTransportAdapter, SimulatorTransportAdapter
from .faults import FaultPolicy
from .protocols import NGXSimulatorProtocol, PychronValveSimulatorProtocol
from .session import load_transport_session


PROTOCOLS = {
    "ngx": NGXSimulatorProtocol,
    "pychron_valve": PychronValveSimulatorProtocol,
}


def build_transport_adapter(
    backend,
    transport_kind="",
    fixture_path=None,
    scenario_path=None,
    mode="strict",
    protocol_name=None,
    seed=1,
    fault_names=None,
    fault_policy=None,
):
    if backend in (None, "", "real"):
        return

    if fault_policy is None:
        fault_policy = FaultPolicy.from_names(fault_names or [])

    path = scenario_path or fixture_path
    if backend == "replay":
        if not path:
            raise ValueError("fixture_path or scenario_path is required for replay")
        session = load_transport_session(path)
        return ReplayTransportAdapter(session=session, mode=mode, fault_policy=fault_policy)

    if backend == "simulator":
        if path:
            manifest = _load_manifest(path)
            protocol_name = manifest.get("protocol", protocol_name)
            seed = manifest.get("seed", seed)
            mode = manifest.get("mode", mode)
            if not fault_names and manifest.get("faults"):
                fault_policy = FaultPolicy(manifest["faults"])

        protocol_name = protocol_name or "pychron_valve"
        try:
            protocol_factory = PROTOCOLS[protocol_name]
        except KeyError as exc:
            raise ValueError(f"unknown simulator protocol {protocol_name!r}") from exc
        return SimulatorTransportAdapter(
            transport_kind=transport_kind,
            protocol=protocol_factory(seed=seed)
            if protocol_name == "ngx"
            else protocol_factory(),
            fault_policy=fault_policy,
        )

    raise ValueError(f"unsupported transport backend {backend!r}")


def _load_manifest(path):
    path = Path(path)
    if path.suffix.lower() == ".json":
        import json

        return json.loads(path.read_text())
    raise ValueError(f"unsupported scenario manifest format {path.suffix}")
