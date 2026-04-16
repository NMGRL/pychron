# ===============================================================================
# Copyright 2011 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================
import json
import logging
import os
import time
from socket import gethostbyname, gethostname, gaierror
from threading import Thread
from typing import Any as TypingAny, Optional

# =============enthought library imports=======================
from apptools.preferences.preference_binding import bind_preference
from pyface.timer.do_later import do_after
from pyface.ui_traits import PyfaceColor
from traits.api import (
    Instance,
    List,
    Any,
    Bool,
    on_trait_change,
    Str,
    Int,
    Dict,
    File,
    Float,
    Enum,
)

from pychron.canvas.canvas_editor import CanvasEditor
from pychron.core.file_listener import FileListener
from pychron.core.ui.gui import invoke_in_main_thread
from pychron.core.wait.wait_group import WaitGroup
from pychron.envisage.consoleable import Consoleable
from pychron.extraction_line import LOG_LEVEL_NAMES, LOG_LEVELS
from pychron.extraction_line.actuation_preview import ActuationPreview
from pychron.extraction_line.canvas.state import (
    CanvasSystemState,
    NetworkSnapshot,
    ValveVisualState,
)
from pychron.extraction_line.canvas.view_model import ExtractionLineCanvasViewModel
from pychron.extraction_line.explanation.extraction_line_explanation import (
    ExtractionLineExplanation,
)
from pychron.extraction_line.extraction_line_canvas import ExtractionLineCanvas
from pychron.extraction_line.graph.extraction_line_graph import ExtractionLineGraph
from pychron.extraction_line.sample_changer import SampleChanger
from pychron.globals import globalv
from pychron.hardware.core.i_core_device import ICoreDevice
from pychron.managers.manager import Manager
from pychron.monitors.system_monitor import SystemMonitor
from pychron.paths import paths
from pychron.pychron_constants import NULL_STR

MANAGERS = {
    "manometer_manager": (
        "pychron.extraction_line.manometer_manager",
        "ManometerManager",
    ),
    "cryo_manager": ("pychron.extraction_line.cryo_manager", "CryoManager"),
    "gauge_manager": ("pychron.extraction_line.gauge_manager", "GaugeManager"),
    "heater_manager": ("pychron.extraction_line.heater_manager", "HeaterManager"),
    "pump_manager": ("pychron.extraction_line.pump_manager", "PumpManager"),
}


class ExtractionLineManager(Manager, Consoleable):
    """
    Manager for interacting with the extraction line
    contains reference to valve manager, gauge manager and laser manager

    """

    canvas = Instance(ExtractionLineCanvas)
    canvases = List

    plugin_canvases = List

    explanation = Instance(ExtractionLineExplanation, ())
    canvas_view_model = Instance(ExtractionLineCanvasViewModel, ())
    monitor = Instance(SystemMonitor)

    switch_manager = Any
    gauge_manager = Any
    cryo_manager = Any
    multiplexer_manager = Any
    manometer_manager = Any
    pump_manager = Any
    heater_manager = Any

    network = Instance(ExtractionLineGraph)
    readback_items = List

    runscript = None
    learner = None

    mode = "normal"

    valve_state_frequency = Int
    valve_lock_frequency = Int

    check_master_owner = Bool
    use_network = Bool
    display_volume = Bool
    volume_key = Str

    sample_changer = Instance(SampleChanger)
    link_valve_actuation_dict = Dict

    canvas_path = File
    canvas_config_path = File

    use_hardware_update = Bool
    hardware_update_period = Float

    file_listener = None

    wait_group = Instance(WaitGroup, ())
    console_bgcolor = PyfaceColor("black")

    _active = False
    _update_status_flag = None
    _monitoring_valve_status = False
    _hardware_update_timer = None
    _initial_canvas_sync_timer = None

    canvas_editor = Instance(CanvasEditor, ())
    logging_level = Enum(LOG_LEVEL_NAMES)
    canvas_state = Instance(CanvasSystemState, ())
    network_snapshot = Instance(NetworkSnapshot, ())

    def set_extract_state(self, *args, **kw):
        pass

    def activate(self):
        self.bind_preferences()
        self._active = True
        self._load_additional_canvases()
        self._activate_hook()

        self.reload_canvas()
        devs = self.application.get_services(ICoreDevice)
        self.devices = devs

    def deactivate(self) -> None:
        if self.switch_manager:
            try:
                self.switch_manager._save_states()
            except BaseException as e:
                self.warning("failed saving soft lock states on deactivate: {}".format(e))

        for t in ("gauge", "heater", "pump"):
            self.info("start {} scans".format(t))
            man = getattr(self, "{}_manager".format(t))
            if man:
                man.stop_scans()

        if self.monitor:
            self.monitor.stop()
        self._active = False
        self._cancel_delayed_updates()
        self._deactivate_hook()

    def bind_preferences(self):
        prefid = "pychron.extraction_line"

        attrs = (
            "canvas_path",
            "canvas_config_path",
            "use_hardware_update",
            "hardware_update_period",
            "check_master_owner",
            "use_network",
            "logging_level",
        )

        for attr in attrs:
            try:
                bind_preference(self, attr, "{}.{}".format(prefid, attr))
            except BaseException as e:
                self.warning("failed binding extraction line preference {}. {}".format(attr, e))

        bind_preference(self.network, "inherit_state", "{}.inherit_state".format(prefid))

        self.console_bind_preferences("{}.console".format(prefid))

        for t in ("gauge", "heater", "pump"):
            man = getattr(self, "{}_manager".format(t))
            if man:
                bind_preference(
                    man,
                    "period",
                    "{}.{}_update_period".format(prefid, t),
                )
                bind_preference(
                    man,
                    "update_enabled",
                    "{}.{}_update_enabled".format(prefid, t),
                )

        if self.canvas:
            bind_preference(
                self.canvas.canvas2D,
                "display_volume",
                "{}.display_volume".format(prefid),
            )
            bind_preference(self.canvas.canvas2D, "volume_key", "{}.volume_key".format(prefid))

    def link_valve_actuation(self, name, func, remove=False):
        if remove:
            try:
                del self.link_valve_actuation_dict[name]
            except KeyError:
                self.debug(
                    'could not remove "{}". not in dict {}'.format(
                        name, ",".join(list(self.link_valve_actuation_dict.keys()))
                    )
                )
        else:
            self.debug(
                'adding name="{}", func="{}" to link_valve_actuation_dict'.format(
                    name, func.__name__
                )
            )
            self.link_valve_actuation_dict[name] = func

    def toggle_auto_reload(self) -> None:
        if self.file_listener:
            self.file_listener.stop()
            self.file_listener = None
        else:
            self.file_listener = FileListener(path=self.canvas_path, callback=self.reload_canvas)

    def disable_auto_reload(self):
        if self.file_listener:
            self.file_listener.stop()

    def do_sample_loading(self):
        """
        1. isolate chamber
        2.
        :return:
        """
        sc = self._sample_changer_factory()
        if sc:
            if self.confirmation_dialog("Ready to Isolate Chamber"):
                self._handle_console_message(("===== Isolate Chamber =====", "maroon"))
                if not sc.isolate_chamber():
                    return
            else:
                return

            if self.confirmation_dialog("Ready to Evacuate Chamber"):
                self._handle_console_message(("===== Evacuate Chamber =====", "maroon"))
                err = sc.check_evacuation()
                if err:
                    name = sc.chamber
                    msg = "Are you sure you want to evacuate the {} chamber. {}".format(name, err)
                    if not self.confirmation_dialog(msg):
                        return

                if not sc.evacuate_chamber():
                    return

            else:
                return

            if self.confirmation_dialog("Ready to Finish Sample Change"):
                self._handle_console_message(("===== Finish Sample Change =====", "maroon"))
                sc.finish_chamber_change()

    def get_volume(self, node_name: str) -> float:
        v = 0
        if self.use_network:
            snapshot = self.network_snapshot
            if snapshot is None:
                snapshot = self.network.compute_state()
                self.network_snapshot = snapshot

            valve_state = snapshot.valves.get(node_name)
            if valve_state is not None:
                if valve_state.side_volumes:
                    v = max(valve_state.side_volumes) + valve_state.valve_volume
                else:
                    v = valve_state.region_volume

        return v

    def test_cryo_communication(self):
        self.info("test cryo communication")
        ret, err = True, ""
        if self.cryo_manager:
            if self.cryo_manager.simulation:
                ret = globalv.communication_simulation
            else:
                ret = self.cryo_manager.test_connection()
        return ret, err

    def test_gauge_communication(self):
        self.info("test gauge communication")
        ret, err = True, ""
        if self.gauge_manager:
            if self.gauge_manager.simulation:
                ret = globalv.communication_simulation
            else:
                ret = self.gauge_manager.test_connection()
        return ret, err

    def test_connection(self):
        self.info("test connection")
        return self.test_valve_communication()

    def test_valve_communication(self):
        self.info("test valve communication")
        ret, err = True, ""
        if self.switch_manager:
            if hasattr(self.switch_manager, "get_state_checksum"):
                valves = self.switch_manager.switches
                vkeys = sorted(valves.keys())
                state = self.switch_manager.get_state_checksum(vkeys)
                ret = bool(state)
        return ret, err

    def setup_status_monitor(self):
        self.stop_status_monitor(id(self), block=True)
        self.start_status_monitor(id(self))
        self.refresh_states()

    def stop_status_monitor(self, *args, **kw):
        pass

    def start_status_monitor(self, *args, **kw):
        pass

    def refresh_states(self, *args, **kw):
        pass

    def refresh_canvas(self):
        # self.debug('refresh canvas')
        for ci in self.canvases:
            ci.refresh()

    def build_canvas_state(self, snapshot: Optional[NetworkSnapshot] = None) -> CanvasSystemState:
        valves = {}
        degraded_devices = []
        selected_name = ""
        if self.canvas_view_model.selected_item is not None:
            selected_name = getattr(self.canvas_view_model.selected_item, "name", "") or ""

        active_name = ""
        if self.canvas_view_model.active_item is not None:
            active_name = getattr(self.canvas_view_model.active_item, "name", "") or ""

        sm = self.switch_manager
        if snapshot is None and self.use_network:
            snapshot = self.network.compute_state()
        if snapshot is None:
            snapshot = NetworkSnapshot()

        if sm is not None:
            names = set(sm.switches.keys())
            child_map = {}
            for switch in sm.switches.values():
                if switch.parent:
                    child_map.setdefault(switch.parent, []).append(switch.display_name)

            for name in names:
                switch = sm.switches[name]
                connected_volume = 0
                region_id = ""
                dominant_source = ""
                dominant_source_node = ""
                blocked_boundaries = []
                side_volumes = []
                if self.use_network:
                    network_valve = snapshot.valves.get(name)
                    if network_valve is not None:
                        if network_valve.side_volumes:
                            connected_volume = (
                                max(network_valve.side_volumes) + network_valve.valve_volume
                            )
                        else:
                            connected_volume = network_valve.region_volume or 0
                        region_id = network_valve.region_id or ""
                        dominant_source = network_valve.dominant_source or ""
                        dominant_source_node = network_valve.dominant_source_node or ""
                        blocked_boundaries = list(network_valve.blocked_boundaries or [])
                        side_volumes = list(network_valve.side_volumes or [])

                valves[name] = ValveVisualState(
                    name=name,
                    is_open=switch.state,
                    is_locked=switch.software_lock,
                    is_owned=bool(switch.owner),
                    owner=switch.owner or "",
                    is_forced=False,
                    is_interlocked=bool(
                        any(
                            sm.get_switch_by_name(interlock).state
                            for interlock in switch.interlocks
                            if sm.get_switch_by_name(interlock) is not None
                        )
                        or sm._check_positive_interlocks(name)
                    ),
                    is_stale=switch.state is None,
                    last_state_timestamp=switch.last_actuation or "",
                    last_readback_timestamp=switch.last_actuation or "",
                    state_source=("simulated" if globalv.communication_simulation else "hardware"),
                    can_actuate=not switch.software_lock and not bool(switch.owner),
                    cannot_actuate_reason=(
                        "Software locked"
                        if switch.software_lock
                        else "Owned by {}".format(switch.owner) if switch.owner else ""
                    ),
                    children=child_map.get(switch.display_name, []),
                    connected_volume=connected_volume,
                    description=switch.description or "",
                    address=getattr(switch, "address", "") or "",
                    network_region_id=region_id,
                    network_dominant_source=dominant_source,
                    network_dominant_source_node=dominant_source_node,
                    network_blocked_boundaries=blocked_boundaries,
                    network_side_volumes=side_volumes,
                )

        if self.devices:
            degraded_devices = [
                dev.name for dev in self.devices if hasattr(dev, "enabled") and not dev.enabled
            ]

        refresh_age_seconds = 0
        if sm is not None:
            timestamps = [
                switch.last_actuation for switch in sm.switches.values() if switch.last_actuation
            ]
            if timestamps:
                try:
                    last = max(timestamps)
                    refresh_age_seconds = max(
                        time.time()
                        - time.mktime(time.strptime(last.split(".")[0], "%Y-%m-%dT%H:%M:%S")),
                        0,
                    )
                except BaseException:
                    refresh_age_seconds = 0

        return CanvasSystemState(
            valves=valves,
            active_item=active_name,
            selected_item=selected_name,
            degraded_devices=degraded_devices,
            network_regions=snapshot.regions or {},
            network=snapshot,
            network_region_count=snapshot.region_count or 0,
            blocked_boundaries=list(snapshot.blocked_boundaries or []),
            recent_events=[],
            refresh_age_seconds=refresh_age_seconds,
            simulation_mode=globalv.communication_simulation,
        )

    def push_canvas_state(self, refresh: bool = False) -> CanvasSystemState:
        snapshot = None
        if self.use_network:
            snapshot = self.network.compute_state()
        self.network_snapshot = snapshot or NetworkSnapshot()

        state = self.build_canvas_state(snapshot=snapshot)
        self.canvas_state = state
        self.canvas_view_model.set_state(state)
        for canvas in self.canvases:
            canvas.apply_canvas_state(state, refresh=refresh)
        return state

    def finish_loading(self) -> None:
        if self.use_network:
            self.network.load(self.canvas_path)
            self.network_snapshot = self.network.compute_state()
        self._set_logger_level(self.switch_manager)

    def reload_canvas(self) -> None:
        self.debug("reload canvas")
        self.reload_scene_graph()
        if self.use_network:
            self.network.load(self.canvas_path)
            self.network_snapshot = self.network.compute_state()

        sm = self.switch_manager
        if sm:
            sm.refresh_network()
            for p in sm.pipette_trackers:
                p.load()

            for p in sm.pipette_trackers:
                self._set_pipette_counts(p.name, p.counts)

        self._reload_canvas_hook()

        self.push_canvas_state(refresh=True)
        self.refresh_canvas()

    def reload_scene_graph(self):
        self.info("reloading canvas scene")
        for c in self.canvases:
            # c.load_canvas_file(c.config_name)

            c.load_canvas_file()
            if self.switch_manager:
                for k, v in self.switch_manager.switches.items():
                    vc = c.get_object(k)
                    if vc:
                        vc.soft_lock = v.software_lock
                        vc.state = v.state

            self.canvas_editor.load(c.canvas2D, self.canvas_path)
        self.push_canvas_state(refresh=True)

    def update_switch_state(self, name, state, *args, refresh: bool = True, **kw) -> None:
        # self.debug('update switch state {} {} args={} kw={}'.format(name, state, args, kw))

        if self.use_network:
            self.network.set_valve_state(name, state)
        self.push_canvas_state(refresh=refresh)

    def update_switch_lock_state(self, *args, **kw) -> None:
        self.push_canvas_state(refresh=True)

    def update_switch_owned_state(self, *args, **kw) -> None:
        self.push_canvas_state(refresh=True)

    def set_valve_owner(self, name, owner):
        """
        set flag indicating if the valve is owned by a system
        """
        if self.switch_manager is not None:
            self.switch_manager.set_valve_owner(name, owner)

    def show_valve_properties(self, name):
        if self.switch_manager is not None:
            self.switch_manager.show_valve_properties(name)

    def get_software_lock(self, name, **kw):
        if self.switch_manager is not None:
            return self.switch_manager.get_software_lock(name, **kw)

    def set_software_lock(self, name, lock):
        if self.switch_manager is not None:
            if lock:
                self.switch_manager.lock(name)
            else:
                self.switch_manager.unlock(name)

            description = self.switch_manager.get_switch_by_name(name).description
            self.info(
                "{} ({}) {}".format(name, description, "lock" if lock else "unlock"),
                color="blue" if lock else "black",
            )
            self.update_switch_lock_state(name, lock)

    def get_state_checksum(self, vkeys):
        if self.switch_manager is not None:
            return self.switch_manager.calculate_checksum(vkeys)

    def get_valve_owners(self):
        if self.switch_manager is not None:
            return self.switch_manager.get_owners()

    def get_locked(self):
        if self.switch_manager is not None:
            return self.switch_manager.get_locked()

    def get_valve_lock_states(self):
        if self.switch_manager is not None:
            return self.switch_manager.get_software_locks()

    def get_valve_state(self, name=None, description=None):
        if self.switch_manager is not None:
            if description is not None and description.strip():
                return self.switch_manager.get_state_by_description(description)
            else:
                return self.switch_manager.get_state_by_name(name)

    def get_indicator_state(self, name=None, description=None):
        if self.switch_manager is not None:
            if description is not None and description.strip():
                return self.switch_manager.get_indicator_state_by_description(description)
            else:
                return self.switch_manager.get_indicator_state_by_name(name)

    def get_valve_states(self):
        if self.switch_manager is not None:
            # only query valve states if not already doing a
            # hardware_update via _trigger_update
            return self.switch_manager.get_states(query=not self.use_hardware_update)

    def get_state_word(self):
        if self.switch_manager is not None:
            # only query valve states if not already doing a
            # hardware_update via _trigger_update
            return self.switch_manager.get_states(query=not self.use_hardware_update, version=1)

    def get_lock_word(self):
        if self.switch_manager is not None:
            # only query valve states if not already doing a
            # hardware_update via _trigger_update
            return self.switch_manager.get_software_locks(version=1)

    def get_valve_by_name(self, name):
        if self.switch_manager is not None:
            return self.switch_manager.get_switch_by_name(name)

    def get_valve_names(self):
        names = []
        if self.switch_manager is not None:
            names = self.switch_manager.get_valve_names()
        return names

    def get_pipette_counts(self):
        counts = []
        if self.switch_manager is not None:
            counts = self.switch_manager.get_pipette_counts()
        return counts

    def get_pipette_count(self, name):
        count = 0
        if self.switch_manager is not None:
            count = self.switch_manager.get_pipette_count(name)
        return count

    def get_pressure(self, controller, name):
        if self.gauge_manager:
            return self.gauge_manager.get_pressure(controller, name)

    def get_device_value(self, dev_name):
        dev = self.get_device(dev_name)
        if dev is None:
            self.unique_warning("No device named {}".format(dev_name))
        else:
            return dev.get()

    def disable_valve(self, description):
        self._enable_valve(description, False)

    def enable_valve(self, description):
        self._enable_valve(description, True)

    def lock_valve(self, name, **kw):
        return self._lock_valve(name, True, **kw)

    def unlock_valve(self, name, **kw):
        return self._lock_valve(name, False, **kw)

    def open_valve(self, name, **kw):
        return self._open_close_valve(name, "open", **kw)

    def close_valve(self, name, **kw):
        return self._open_close_valve(name, "close", **kw)

    def preview_open_valve(self, name, description=None, address=None, sender_address=None):
        """Dry-run preview of opening a valve. Returns ActuationPreview."""
        return self._preview_actuation(name, "open", description, address, sender_address)

    def preview_close_valve(self, name, description=None, address=None, sender_address=None):
        """Dry-run preview of closing a valve. Returns ActuationPreview."""
        return self._preview_actuation(name, "close", description, address, sender_address)

    def _preview_actuation(self, name, action, description=None, address=None, sender_address=None):
        """Build an ActuationPreview without executing the actuation."""
        vm = self.switch_manager
        preview = ActuationPreview(
            requested_action=action,
            valve_name=name,
            current_state=None,
        )

        if vm is None:
            preview.allowed = False
            preview.reasons_blocking.append("Switch manager not available")
            preview.warning_level = "error"
            return preview

        resolved = self._resolve_switch_name(name, description=description, address=address)
        if not resolved:
            preview.allowed = False
            preview.reasons_blocking.append("Valve '{}' not found".format(name))
            preview.warning_level = "error"
            return preview

        preview.valve_name = resolved
        valve = vm.get_switch_by_name(resolved)
        if valve is None:
            preview.allowed = False
            preview.reasons_blocking.append("Valve '{}' not found".format(resolved))
            preview.warning_level = "error"
            return preview

        preview.current_state = valve.state
        preview.is_soft_locked = valve.software_lock
        preview.is_enabled = getattr(valve, "enabled", True)
        preview.owner = valve.owner or ""

        # Check if already in target state
        target_state = action == "open"
        if valve.state == target_state:
            preview.allowed = False
            preview.reasons_blocking.append(
                "Valve is already {}".format("open" if target_state else "closed")
            )
            preview.warning_level = "info"
            return preview

        # Check soft lock
        if valve.software_lock:
            preview.allowed = False
            preview.reasons_blocking.append("Software locked")
            preview.warning_level = "warning"
            return preview

        # Check enabled
        if not getattr(valve, "enabled", True):
            preview.allowed = False
            preview.reasons_blocking.append("Valve not enabled")
            preview.warning_level = "warning"
            return preview

        # Check ownership
        if not self._check_ownership(resolved, sender_address):
            preview.allowed = False
            preview.reasons_blocking.append("Owned by {}".format(valve.owner))
            preview.warning_level = "warning"
            return preview

        # Check soft interlocks
        if action == "open":
            interlocked = vm._check_soft_interlocks(resolved)
            if interlocked:
                preview.allowed = False
                preview.reasons_blocking.append("Interlock: {} is open".format(interlocked.name))
                preview.warning_level = "error"
                return preview

            positive = vm._check_positive_interlocks(resolved)
            if positive:
                preview.allowed = False
                preview.interlocks = positive
                preview.reasons_blocking.append(
                    "Positive interlocks not enabled: {}".format(", ".join(positive))
                )
                preview.warning_level = "warning"
                return preview
        else:
            interlocked = vm._check_soft_interlocks(resolved)
            if interlocked:
                preview.allowed = False
                preview.reasons_blocking.append("Interlock: {} is open".format(interlocked.name))
                preview.warning_level = "error"
                return preview

        # Collect affected children
        children = vm.get_children(resolved)
        if children:
            preview.affected_children = [c.name for c in children]

        # Network region changes
        if self.use_network and self.network:
            try:
                snapshot = self.network.compute_state()
                if snapshot and resolved in snapshot.valves:
                    nv = snapshot.valves[resolved]
                    if nv.side_volumes:
                        preview.network_region_changes = [
                            "Volume changes from {:0.1f} to {:0.1f} cc".format(
                                min(nv.side_volumes), max(nv.side_volumes) + nv.valve_volume
                            )
                        ]
                    if nv.region_id:
                        preview.network_region_changes.append("Region: {}".format(nv.region_id))
            except BaseException:
                pass

        # Determine if confirmation is needed
        if preview.affected_children or preview.network_region_changes:
            preview.requires_confirmation = True
            preview.warning_level = "info"

        return preview

    def sample(self, name, **kw):
        def sample():
            valve = self.switch_manager.get_switch_by_name(name)
            if valve is not None:
                self.info("start sample")
                self.open_valve(name, **kw)
                time.sleep(valve.sample_period)

                self.info("end sample")
                self.close_valve(name, **kw)

        t = Thread(target=sample)
        t.start()

    # ------------------------------------------------------------
    # Aqua
    # ------------------------------------------------------------
    script_executor = None
    _aqua_active_flag = False

    def aqua_trigger(self):
        app = self.application
        se = self.script_executor
        if not se:
            se = app.get_service("pychron.pyscripts.tasks.pyscript_task.ScriptExecutor")
            self.script_executor = se
        # context = {"analysis_type": "blank" if "blank" in name else "unknown"}
        name = "aqua.py"
        root = os.path.join(paths.scripts_dir)
        p = os.path.join(root, name)
        if os.path.isfile(p):
            context = {}
            se.execute_script(name, root, delay_start=1, manager=self, context=context, kind="Aqua")
            self._aqua_active_flag = True
        else:
            self.warning(f"{p} is not a valid file")

    def aqua_get_status(self):
        status = {}
        if self.script_executor and self._aqua_active_flag:
            status = self.script_executor.get_script_status()
            if status.get("completed"):
                self._aqua_active_flag = False
        return json.dumps(status)

    def aqua_get_report(self):
        if self.script_executor:
            # get the last entry in the aqua log file and send
            pass

    def cycle(self, name, **kw):
        def cycle():
            valve = self.switch_manager.get_switch_by_name(name)
            if valve is not None:
                n = valve.cycle_n
                period = valve.cycle_period

                self.info("start cycle n={} period={}".format(n, period))
                for i in range(n):
                    self.info("valve cycling iteration ={}".format(i + 1))
                    self.open_valve(name, **kw)
                    time.sleep(period)
                    self.close_valve(name, **kw)
                    time.sleep(period)

        t = Thread(target=cycle)
        t.start()

    def get_script_state(self, key):
        return self.pyscript_editor.get_script_state(key)

    def set_selected_explanation_item(self, obj):
        if self.explanation:
            selected = None
            if obj:
                selected = next(
                    (i for i in self.explanation.explanable_items if obj.name == i.name),
                    None,
                )

            self.explanation.selected = selected
        name = getattr(obj, "name", "") if obj else ""
        self.canvas_view_model.set_selected_item(name)

    def set_active_canvas_item(self, obj):
        name = getattr(obj, "name", "") if obj else ""
        self.canvas_view_model.set_active_item(name)

    def new_canvas(self, config: Optional[str] = None) -> ExtractionLineCanvas:
        c = ExtractionLineCanvas(manager=self, display_name="Extraction Line")
        c._pending_canvas_config = config
        self.canvases.append(c)
        c.canvas2D.trait_set(display_volume=self.display_volume, volume_key=self.volume_key)
        if self.switch_manager:
            self.switch_manager.load_valve_states()
            self.switch_manager.load_valve_lock_states(force=True)
            self.switch_manager.load_valve_owners()

        self._schedule_initial_canvas_sync(0)

        return c

    def get_wait_control(self):
        return self.wait_group.get_wait_control()

    def set_experiment_type(self, v):
        self.debug("setting experiment type={}".format(v))
        if self.cryo_manager:
            self.cryo_manager.species = v

    # =========== Cryo ==============================================================
    def set_cryo(self, v, v2=None, **kw):
        self.debug("setting cryo to {}, {}".format(v, v2))
        if self.cryo_manager:
            return self.cryo_manager.set_setpoint(v, v2, **kw)
        else:
            self.warning("cryo manager not available")
            return 0, 0

    def get_cryo_temp(self, iput):
        self.debug("get cryo temp {}".format(iput))
        if self.cryo_manager:
            return self.cryo_manager.read_input(iput)
        else:
            self.warning("cryo manager not available")
            return 0

    def get_cryo_response_blob(self):
        if self.cryo_manager:
            return self.cryo_manager.response_recorder.get_response_blob()

    def start_cryo_recorder(self):
        if self.cryo_manager:
            self.cryo_manager.start_response_recorder()

    def stop_cryo_recorder(self):
        if self.cryo_manager:
            self.cryo_manager.stop_response_recorder()

    # ===============================================================================

    # ============= Manometer =======================================================
    def get_manometer_pressure(self, idx=0):
        self.debug("get manometer pressure")
        ret = 0
        if self.manometer_manager:
            ret = self.manometer_manager.get_pressure(idx)
        else:
            self.warning("manometer manager not available")
        return ret

    # ===============================================================================

    # ===============================================================================
    # private
    # ===============================================================================
    def _load_additional_canvases(self):
        for ci in self.plugin_canvases:
            c = ExtractionLineCanvas(
                manager=self,
                display_name=ci["display_name"],
            )
            c.load_canvas_file(ci["canvas_path"], ci["config_path"], ci["valve_path"])
            self.canvases.append(c)

    def _activate_hook(self):
        self.monitor = SystemMonitor(manager=self, name="system_monitor")
        self.monitor.monitor()

        # start the managers 'a scanning
        for t in ("gauge", "heater", "pump"):
            self.info("start {} scans".format(t))
            man = getattr(self, "{}_manager".format(t))
            if man:
                man.start_scans()

        if self.switch_manager and self.use_hardware_update:
            self._schedule_hardware_update(1000)

    def _update(self):
        if self.use_hardware_update and self._active:
            rc = self.switch_manager.load_hardware_states(refresh_canvas=False)
            rc = self.switch_manager.load_valve_owners(refresh_canvas=False) or rc

            if self.canvas.canvas2D.scene.widgets:
                # update registered widgets
                for widget in self.canvas.canvas2D.scene.widgets.values():
                    try:
                        rc = widget.update() or rc
                    except BaseException as e:
                        self.critical("failed updating widget {}, {}".format(widget, e))
            if rc:
                self.refresh_canvas()

            self._schedule_hardware_update(self.hardware_update_period * 1000)

    def _cancel_delayed_updates(self) -> None:
        for attr in ("_hardware_update_timer", "_initial_canvas_sync_timer"):
            timer = getattr(self, attr, None)
            if timer is None:
                continue

            for method_name in ("cancel", "stop"):
                method = getattr(timer, method_name, None)
                if method is None:
                    continue
                try:
                    method()
                except BaseException as e:
                    self.debug(
                        "failed canceling delayed update {} using {}: {}".format(
                            attr, method_name, e
                        )
                    )
                break

            setattr(self, attr, None)

    def _schedule_do_after(
        self, attr: str, delay: TypingAny, func: TypingAny
    ) -> TypingAny:
        timer = getattr(self, attr, None)
        if timer is not None:
            cancel = getattr(timer, "cancel", None)
            if cancel is not None:
                try:
                    cancel()
                except BaseException:
                    pass

        timer = do_after(delay, func)
        setattr(self, attr, timer)
        return timer

    def _schedule_hardware_update(self, delay: TypingAny) -> None:
        self._schedule_do_after("_hardware_update_timer", delay, self._update)

    def _schedule_initial_canvas_sync(self, delay: TypingAny) -> None:
        self._schedule_do_after(
            "_initial_canvas_sync_timer", delay, self._sync_initial_canvas_state
        )

    def _deactivate_hook(self):
        pass

    def _reload_canvas_hook(self):
        pass

    def _log_spec_event(self, name, action):
        sm = self.application.get_service("pychron.spectrometer.scan_manager.ScanManager")
        if sm:
            color = 0x98FF98 if action == "open" else 0xFF9A9A
            sm.add_spec_event_marker(
                "{} ({})".format(name, action), mode="valve", extra=name, bgcolor=color
            )

        # Log valve operation to Prometheus observability
        try:
            from pychron.observability import event_capture

            event_capture.add_event(
                event_type="counter",
                metric_name=f"valve_{action}",
                value=1.0,
                labels={"valve": name},
                status="success",
            )
        except Exception as e:
            self.debug(f"Failed to log valve event to Prometheus: {e}")

    def _enable_valve(self, description, state):
        if self.switch_manager:
            valve = self.switch_manager.get_valve_by_description(description)
            if valve is None:
                valve = self.switch_manager.get_switch_by_name(description)

            if valve is not None:
                if not state:
                    self.close_valve(valve.name)

                valve.enabled = state

    def _lock_valve(self, name, action, description=None, address=None, **kw):
        """

        :param name:
        :param action: bool True ==lock false ==unlock
        :param description:
        :param kw:
        :return:
        """
        vm = self.switch_manager
        if vm is not None:
            oname = name
            if address:
                name = vm.get_name_by_address(address)

            if description and description != NULL_STR:
                name = vm.get_name_by_description(description, name=name)

            if not name:
                self.warning("Invalid valve name={}, description={}".format(oname, description))
                return False

            v = vm.get_switch_by_name(name)
            if action:
                v.lock()
            else:
                v.unlock()

            self.update_switch_lock_state(name, action)
            self.refresh_canvas()
            return True

    def _open_close_valve(self, name, action, description=None, address=None, mode="remote", **kw):
        vm = self.switch_manager
        if vm is not None:
            oname = name
            name = self._resolve_switch_name(name, description=description, address=address)
            if not name:
                self.warning("Invalid valve name={}, description={}".format(oname, description))
                return False, False

            result = self._change_switch_state(name, mode, action, **kw)
            self.debug("open_close_valve, mode={} result={}".format(mode, result))
            if result:
                self._handle_actuation_result(name, action, mode, result, emit_event=True)

            return result

        return True, True

    def _change_switch_state(self, name, mode, action, sender_address=None, **kw):
        result, change = False, False
        if self._check_ownership(name, sender_address):
            func = getattr(self.switch_manager, "{}_by_name".format(action))
            ret = func(name, mode=mode, **kw)
            self.debug("change switch state name={} action={} ret={}".format(name, action, ret))
            if ret:
                result, change = ret
                if isinstance(result, bool):
                    if change:
                        self.update_switch_state(name, True if action == "open" else False)
        return result, change

    def _resolve_switch_name(self, name, description=None, address=None):
        vm = self.switch_manager
        if vm is None:
            return

        resolved = name
        if address:
            resolved = vm.get_name_by_address(address)

        if description and description != NULL_STR:
            resolved = vm.get_name_by_description(description, resolved)

        return resolved

    def _handle_actuation_result(
        self, name, action, mode, result, include_children=True, emit_event=False
    ):
        if not all(result):
            return

        vm = self.switch_manager
        valve = vm.get_switch_by_name(name) if vm is not None else None
        if valve is None:
            return

        if emit_event:
            self._log_spec_event(name, action)
        self.info(
            "{:<6s} {} ({})".format(action.upper(), valve.name, valve.description),
            color="red" if action == "close" else "green",
        )
        self._notify_linked_valve_actuation(name, action)

        if include_children and vm is not None:
            for child_name, child_result in vm.actuate_children(name, action, mode):
                if child_result:
                    self._handle_actuation_result(
                        child_name,
                        action,
                        mode,
                        child_result,
                        include_children=False,
                        emit_event=False,
                    )

    def _notify_linked_valve_actuation(self, name, action):
        ld = self.link_valve_actuation_dict
        if not ld:
            return

        try:
            func = ld[name]
        except KeyError:
            self.debug(
                'name="{}" not in link_valve_actuation_dict. keys={}'.format(
                    name, ",".join(list(ld.keys()))
                )
            )
            return

        func(name, action)

    def _check_ownership(self, name, requestor, force=False):
        """
        check if this valve is owned by
        another client

        if this is not a client but you want it to
        respect valve ownership
        set check_master_owner=True

        """
        ret = True

        if force or self.check_master_owner:
            if requestor is None:
                try:
                    requestor = gethostbyname(gethostname())
                except gaierror:
                    self.debug("failed to get host name. defaulting to 'localhost'")
                    requestor = "localhost"

            self.debug("checking ownership. requestor={}".format(requestor))
            try:
                v = self.switch_manager.switches[name]
                ret = not (v.owner and v.owner != requestor)
            except KeyError:
                pass
        return ret

    def _set_pipette_counts(self, name, value):
        for c in self.canvases:
            scene = c.canvas2D.scene
            obj = scene.get_item("vlabel_{}".format(name))
            if obj is not None:
                obj.value = int(value)
                c.refresh()

    def _sample_changer_factory(self):
        sc = self.sample_changer
        if sc is None:
            sc = SampleChanger(manager=self)

        if sc.setup():
            result = sc.edit_traits(view="chamber_select_view")
            if result:
                if sc.chamber and sc.chamber != NULL_STR:
                    self.sample_changer = sc
                    return sc

    def _create_manager(self, klass, manager, params, **kw):
        # try a lazy load of the required module
        # if 'fusions' in manager:
        # package = 'pychron.managers.laser_managers.{}'.format(manager)
        # self.laser_manager_id = manager
        if "rpc" in manager:
            package = "pychron.rpc.manager"
        else:
            package = "pychron.managers.{}".format(manager)

        if manager in (
            "switch_manager",
            "gauge_manager",
            "multiplexer_manager",
            "cryo_manager",
            "manometer_manager",
            "heater_manager",
            "pump_manager",
        ):
            if manager == "switch_manager":
                man = self._switch_manager_factory()
                self.switch_manager = man
                return man
            else:
                package, klass = MANAGERS[manager]
                factory = self.get_manager_factory(package, klass)
                man = factory(application=self.application)
                setattr(self, manager, man)
                return man
                # return getattr(self, manag/er)
        else:
            class_factory = self.get_manager_factory(package, klass, warn=False)
            if class_factory is None:
                package = "pychron.extraction_line.{}".format(manager)
                class_factory = self.get_manager_factory(package, klass)
            if class_factory:
                m = class_factory(**params)
                self.add_trait(manager, m)
                return m
            else:
                self.debug(
                    "could not create manager {}, {},{},{}".format(klass, manager, params, kw)
                )

    def _set_logger_level(self, obj=None):
        level = LOG_LEVELS.get(self.logging_level, logging.DEBUG)
        if obj:
            getattr(obj, "logger").setLevel(level)
            if hasattr(obj, "set_logger_level_hook"):
                obj.set_logger_level_hook(level)

    # ===============================================================================
    # handlers
    # ===============================================================================
    def _logging_level_changed(self, new):
        if new:
            self._set_logger_level(self)
            if self.switch_manager:
                self._set_logger_level(self.switch_manager)

    @on_trait_change("use_hardware_update")
    def _update_use_hardware_update(self):
        if self.use_hardware_update:
            self._schedule_hardware_update(1000)
        else:
            self._cancel_delayed_updates()

    # @on_trait_change('switch_manager:pipette_trackers:counts')
    def _update_pipette_counts(self, obj, name, old, new):
        self._set_pipette_counts(obj.name, new)

    @on_trait_change("use_network,network:inherit_state")
    def _sync_initial_canvas_state(self) -> None:
        self._initial_canvas_sync_timer = None
        for c in self.canvases:
            if getattr(c.canvas2D, "control", None) is None:
                self._schedule_initial_canvas_sync(100)
                return

        for c in self.canvases:
            config = getattr(c, "_pending_canvas_config", None)
            c.load_canvas_file(canvas_config_path=config)

        if self.use_network:
            self._update_network(refresh=False)
        else:
            self.push_canvas_state(refresh=False)

        self.refresh_canvas()

    def _update_network(self, refresh: bool = True) -> None:
        if self.use_network:
            net = self.network
            if self.switch_manager:
                for name, switch in self.switch_manager.switches.items():
                    net.set_valve_state(name, switch.state)
            self.push_canvas_state(refresh=refresh)
        else:
            self.network_snapshot = NetworkSnapshot()
            self.push_canvas_state(refresh=refresh)

    @on_trait_change("display_volume,volume_key")
    def _update_canvas_inspector(self, name, new):
        for c in self.canvases:
            c.canvas2D.trait_set(**{name: new})

    def _handle_state(self, new) -> None:
        # self.debug('handle state {}'.format(new))
        if isinstance(new, tuple):
            self.update_switch_state(*new, refresh=True)
        else:
            n = len(new)
            for i, ni in enumerate(new):
                self.update_switch_state(*ni, refresh=i == n - 1)

    def _handle_lock_state(self, new):
        self.debug("refresh_lock_state fired. {}".format(new))
        self.update_switch_lock_state(*new)

    def _handle_owned_state(self, new):
        self.update_switch_owned_state(*new)

    def _handle_refresh_canvas(self, new):
        # self.debug('refresh_canvas_needed fired')
        self.refresh_canvas()

    def _handle_console_message(self, new):
        color = None
        if isinstance(new, tuple):
            msg, color = new
        else:
            msg = new

        if color is None:
            color = self.console_default_color

        if self.console_display:
            self.console_display.add_text(msg, color=color)

    # ===============================================================================
    # factories
    # ===============================================================================
    def _switch_manager_factory(self):
        klass = self._get_switch_manager_klass()
        vm = klass(application=self.application)
        vm.on_trait_change(self._handle_state, "refresh_state")
        vm.on_trait_change(self._handle_lock_state, "refresh_lock_state")
        vm.on_trait_change(self._handle_owned_state, "refresh_owned_state")
        vm.on_trait_change(self._handle_refresh_canvas, "refresh_canvas_needed")
        vm.on_trait_change(self._handle_console_message, "console_message")
        vm.on_trait_change(self._update_pipette_counts, "pipette_trackers:counts")
        bind_preference(vm, "valves_path", "pychron.extraction_line.valves_path")

        return vm

    def _get_switch_manager_klass(self):
        from pychron.extraction_line.switch_manager import SwitchManager

        return SwitchManager

    def _explanation_default(self):
        e = ExtractionLineExplanation()
        if self.switch_manager is not None:
            e.load(self.switch_manager.switches)
            self.switch_manager.on_trait_change(e.refresh, "refresh_explanation")
        return e

    def _canvas_default(self):
        return self.new_canvas()

    def _network_default(self):
        return ExtractionLineGraph()


if __name__ == "__main__":
    elm = ExtractionLineManager()
    elm.bootstrap()
    elm.canvas.style = "2D"
    elm.configure_traits()

# =================== EOF ================================
