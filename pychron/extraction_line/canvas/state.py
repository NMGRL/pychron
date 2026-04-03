from traits.api import Any, Bool, Dict, Float, HasTraits, Int, List, Str


class NetworkRegionState(HasTraits):
    identifier = Str
    node_names = List(Str)
    edge_names = List(Str)
    boundary_valves = List(Str)
    dominant_source = Str
    dominant_source_node = Str
    volume = Float


class NetworkValveState(HasTraits):
    name = Str
    region_id = Str
    dominant_source = Str
    dominant_source_node = Str
    region_volume = Float
    valve_volume = Float
    side_volumes = List(Float)
    blocked_by_closed = Bool(False)
    blocked_boundaries = List(Str)


class NetworkSnapshot(HasTraits):
    regions = Dict
    valves = Dict
    node_states = Dict
    edge_states = Dict
    node_to_region = Dict
    region_count = Int
    blocked_boundaries = List(Str)


class ValveVisualState(HasTraits):
    name = Str
    is_open = Any
    is_locked = Bool(False)
    is_owned = Bool(False)
    owner = Str
    is_forced = Bool(False)
    is_interlocked = Bool(False)
    is_stale = Bool(False)
    last_state_timestamp = Str
    last_readback_timestamp = Str
    state_source = Str("unknown")
    can_actuate = Bool(True)
    cannot_actuate_reason = Str
    children = List(Str)
    connected_volume = Float
    description = Str
    address = Str
    network_region_id = Str
    network_dominant_source = Str
    network_dominant_source_node = Str
    network_blocked_boundaries = List(Str)
    network_side_volumes = List(Float)

    def summary_state(self) -> str:
        if self.is_open is None:
            return "Unknown"
        return "Open" if self.is_open else "Closed"


class CanvasSystemState(HasTraits):
    valves = Dict
    active_item = Str
    selected_item = Str
    degraded_devices = List(Str)
    network_regions = Dict
    network = Any
    network_region_count = Int
    blocked_boundaries = List(Str)
    recent_events = List
    refresh_age_seconds = Float
    simulation_mode = Bool(False)

    def get_valve(self, name: str):
        return self.valves.get(name)
