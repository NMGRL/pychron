from traits.api import Any, Bool, Dict, Float, HasTraits, List, Str


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

    def summary_state(self):
        if self.is_open is None:
            return "Unknown"
        return "Open" if self.is_open else "Closed"


class CanvasSystemState(HasTraits):
    valves = Dict
    active_item = Str
    selected_item = Str
    degraded_devices = List(Str)
    network_regions = Dict
    recent_events = List
    refresh_age_seconds = Float
    simulation_mode = Bool(False)

    def get_valve(self, name):
        return self.valves.get(name)

