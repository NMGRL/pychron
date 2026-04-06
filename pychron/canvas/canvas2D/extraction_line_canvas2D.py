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

# ============= enthought library imports =======================
import os

from enable.api import Interactor
from enable.enable_traits import Pointer
from pyface.action.menu_manager import MenuManager
from pyface.qt.QtCore import QPoint
from pyface.qt.QtGui import QToolTip
from traits.api import Any, Str, on_trait_change, Bool, List, Event, Instance
from traitsui.menu import Action

from pychron.canvas.canvas2D.overlays.extraction_line_overlay import (
    ExtractionLineInfoTool,
    ExtractionLineInfoOverlay,
)
from pychron.canvas.canvas2D.scene.extraction_line_scene import ExtractionLineScene
from pychron.canvas.canvas2D.scene.primitives.connections import (
    Elbow,
    Connection,
    Fork,
    Cross,
    Tee,
)
from pychron.canvas.canvas2D.scene.primitives.lasers import Laser
from pychron.canvas.canvas2D.scene.primitives.primitives import BorderLine
from pychron.canvas.canvas2D.scene.primitives.valves import (
    RoughValve,
    BaseValve,
    Switch,
    ManualSwitch,
)
from pychron.canvas.scene_viewer import SceneCanvas
from pychron.globals import globalv

W = 2
H = 2


def snap_to_grid(dx, dy, interval):
    dx = round(dx / interval) * interval
    dy = round(dy / interval) * interval
    return dx, dy


class ExtractionLineAction(Action):
    chamber = Str


class ExtractionLineMenuTool(Interactor):
    parent = Any

    def normal_right_down(self, event):
        if event.handled:
            return

        if self.parent is not None:
            self.parent.show_menu(event)


class ExtractionLineCanvas2D(SceneCanvas):
    """ """

    scene_klass = ExtractionLineScene

    use_backbuffer = True
    backbuffer_padding = False
    border_visible = False
    active_item = Any

    selected_id = Str
    show_axes = False
    show_grids = False
    use_zoom = False
    use_pan = False

    manager = Any

    aspect_ratio = 4 / 3.0

    y_range = (-10, 25)

    display_volume = Bool
    volume_key = Str
    confirm_open = Bool(False)

    force_actuate_enabled = True

    drag_pointer = Pointer("bullseye")
    snap_to_grid = True
    grid_interval = 0.5
    edit_mode = Bool(False)
    _constrain = False

    # Selection model
    selected_items = List
    _box_start = Any
    _box_end = Any
    _is_box_selecting = Bool(False)

    _px = None
    _py = None
    canvas_state = Any
    _context_menu = Any

    def __init__(self, *args, **kw):
        super(ExtractionLineCanvas2D, self).__init__(*args, **kw)

        tool = ExtractionLineInfoTool(scene=self.scene, manager=self.manager, component=self)
        overlay = ExtractionLineInfoOverlay(tool=tool, component=self)
        self.tool = tool
        self.tools.append(ExtractionLineMenuTool(component=self, parent=self))
        self.tools.append(tool)
        self.overlays.append(overlay)

    # @caller
    # def invalidate_and_redraw(self):
    #     super(ExtractionLineCanvas2D, self).invalidate_and_redraw()

    def toggle_item_identify(self, name):
        v = self._get_switch_by_name(name)
        if v is not None:
            try:
                v.identify = not v.identify
            except AttributeError:
                pass

    def update_switch_state(self, name, nstate, refresh=True, mode=None):
        """ """
        switch = self._get_switch_by_name(name)
        if switch is not None:
            if switch.state == nstate:
                return
            switch.state = nstate
            if refresh:
                self.invalidate_and_redraw()

    def apply_canvas_state(self, state, refresh: bool = True) -> None:
        self.canvas_state = state
        for name, valve_state in state.valves.items():
            self.set_valve_visual_state(name, valve_state, refresh=False)

        if self.manager and self.manager.use_network and state.network:
            self.apply_network_snapshot(state.network)
        else:
            self._reset_network_visualization()

        if refresh:
            self.invalidate_and_redraw()

    def apply_network_snapshot(self, snapshot) -> None:
        scene = self.scene
        if scene is None or snapshot is None:
            return

        color_by_source = {}
        for state_dict in (snapshot.node_states, snapshot.edge_states):
            for name, payload in state_dict.items():
                obj = scene.get_item(name)
                if obj is None:
                    continue

                color_source = payload.get("dominant_source_node")
                if color_source and color_source not in color_by_source:
                    source_item = scene.get_item(color_source)
                    if source_item is not None:
                        color_by_source[color_source] = source_item.default_color

                is_active = bool(payload.get("is_active"))
                obj.state = is_active
                if obj.state and color_source in color_by_source:
                    obj.active_color = color_by_source[color_source]
                elif hasattr(obj, "default_color"):
                    obj.active_color = obj.default_color

        for valve_name, valve_state in snapshot.valves.items():
            obj = scene.get_item(valve_name)
            if not isinstance(obj, (BaseValve, Switch)):
                continue

            if (
                self.manager
                and self.manager.network
                and self.manager.network.inherit_state
                and getattr(obj, "state", None)
                not in (
                    "closed",
                    False,
                )
            ):
                source = valve_state.dominant_source_node
                if source and source in color_by_source:
                    obj.active_color = color_by_source[source]
                elif hasattr(obj, "oactive_color"):
                    obj.active_color = obj.oactive_color
            elif hasattr(obj, "oactive_color"):
                obj.active_color = obj.oactive_color

        self._propagate_connector_colors()

    def _propagate_connector_colors(self) -> None:
        """Propagate state/color to visual connectors not in the network graph."""
        scene = self.scene
        if scene is None:
            return

        for item in scene.get_items():
            if not isinstance(item, (BorderLine, Connection, Elbow, Tee, Fork, Cross)):
                continue

            attached_items = self._connected_items_for_connector(item)
            if not attached_items:
                attached_items = self._fallback_connected_items(item)

            endpoint_states = [
                bool(getattr(attached, "state", False)) for attached in attached_items
            ]
            color_item = self._preferred_connector_color_item(attached_items)
            color = self._connector_color_for_item(color_item)
            if color is not None:
                item.active_color = color
                item.state = any(endpoint_states)
                continue

            if endpoint_states:
                item.state = any(endpoint_states)
                if hasattr(item, "default_color"):
                    item.active_color = item.default_color

    def _connector_color_for_item(self, item: object) -> object | None:
        if item is None:
            return None

        if isinstance(item, (BaseValve, Switch)) and not bool(getattr(item, "state", False)):
            # Closed valves/switches should not paint nearby connectors from the opposite side.
            return None

        source_item = item
        if isinstance(item, BaseValve):
            source_name = getattr(item, "network_dominant_source_node", "") or ""
            if source_name:
                candidate = self.scene.get_item(source_name)
                if candidate is not None:
                    source_item = candidate

        if hasattr(source_item, "active_color"):
            if bool(getattr(source_item, "state", False)):
                return source_item.active_color
            return source_item.default_color

        if hasattr(source_item, "default_color"):
            return source_item.default_color

        return None

    def _preferred_connector_color_item(self, attached_items: list[object]) -> object | None:
        for attached in attached_items:
            if not isinstance(attached, (BaseValve, Switch)):
                return attached

        for attached in attached_items:
            if self._connector_color_for_item(attached) is not None:
                return attached

        if attached_items:
            return attached_items[0]

        return None

    def _connected_items_for_connector(self, connector: object) -> list[object]:
        scene = self.scene
        if scene is None:
            return []

        attached = []
        for item in scene.get_items():
            if item is connector:
                continue
            if isinstance(item, (BorderLine, Connection, Elbow, Tee, Fork, Cross)):
                continue
            if not hasattr(item, "connections"):
                continue

            if any(c is connector for _, c in getattr(item, "connections", [])):
                attached.append(item)

        return attached

    def _fallback_connected_items(self, connector: object) -> list[object]:
        """Fallback to a geometric lookup if connection links are unavailable."""
        points = []
        for tag in ("start", "end", "left", "right", "mid", "top", "bottom"):
            point = getattr(connector, f"{tag}_point", None)
            if point is not None:
                points.append(point.get_xy())

        if not points:
            return []

        x = sum(px for px, _ in points) / len(points)
        y = sum(py for _, py in points) / len(points)

        scene = self.scene
        if scene is None:
            return []

        candidates = []
        for item in scene.get_items():
            if item is connector:
                continue
            if isinstance(item, (BorderLine, Connection, Elbow, Tee, Fork, Cross)):
                continue
            if not hasattr(item, "connections"):
                continue

            bounds = item.get_bounds() if hasattr(item, "get_bounds") else None
            if bounds is None:
                continue

            x1, y1, x2, y2 = bounds
            if x1 <= x <= x2 and y1 <= y <= y2:
                return [item]

            dx = 0 if x1 <= x <= x2 else min(abs(x - x1), abs(x - x2))
            dy = 0 if y1 <= y <= y2 else min(abs(y - y1), abs(y - y2))
            candidates.append(((dx * dx) + (dy * dy), item))

        if candidates:
            return [min(candidates, key=lambda t: t[0])[1]]
        return []

    def set_valve_visual_state(self, name, visual_state, refresh=True):
        switch = self._get_switch_by_name(name)
        if switch is None or visual_state is None:
            return

        if hasattr(switch, "apply_visual_state"):
            switch.apply_visual_state(visual_state)
        else:
            switch.state = visual_state.is_open

        if refresh:
            self.invalidate_and_redraw()

    def update_switch_owned_state(self, name, owned):
        switch = self._get_switch_by_name(name)
        if switch is not None:
            if switch.owned == owned:
                return
            switch.owned = owned
            self.invalidate_and_redraw()

    def update_switch_lock_state(self, name, lockstate):
        switch = self._get_switch_by_name(name)
        if switch is not None:
            if switch.soft_lock == lockstate:
                return
            switch.soft_lock = lockstate
            self.invalidate_and_redraw()

    def load_canvas_file(self, canvas_path=None, canvas_config_path=None, valves_path=None):
        if canvas_path is None:
            canvas_path = self.manager.application.preferences.get(
                "pychron.extraction_line.canvas_path"
            )
        if canvas_config_path is None:
            canvas_config_path = self.manager.application.preferences.get(
                "pychron.extraction_line.canvas_config_path"
            )
        if valves_path is None:
            valves_path = self.manager.application.preferences.get(
                "pychron.extraction_line.valves_path"
            )

        if canvas_path and os.path.isfile(canvas_path):
            self.scene.load(canvas_path, canvas_config_path, valves_path, self)
            self.invalidate_and_redraw()

    def _over_item(self, event):
        x, y = event.x, event.y
        return self.scene.get_is_in(x, y, exclude=[BorderLine, Elbow, Connection, Fork, Cross, Tee])

    def normal_left_down(self, event):
        event.handled = True

    def normal_left_dclick(self, event):
        event.handled = True

    def normal_mouse_move(self, event):
        item = self._over_item(event)
        if item is not None:
            self.event_state = "select"
            if item != self.active_item:
                self.active_item = item
                if self.manager:
                    self.manager.set_active_canvas_item(item)
            if isinstance(item, (BaseValve, Switch)):
                event.window.set_pointer(self.select_pointer)
        else:
            event.window.control.setToolTip("")
            QToolTip.hideText()

            self.active_item = None
            self.event_state = "normal"
            event.window.set_pointer(self.normal_pointer)
            if self.manager:
                self.manager.set_active_canvas_item(None)

    def select_mouse_move(self, event):
        """ """
        ctrl = event.window.control
        try:
            tt = self.active_item.get_tooltip_text()
            ctrl.setToolTip(tt)
        except AttributeError as e:
            pass
        self.normal_mouse_move(event)

    def select_right_down(self, event):
        item = self.active_item
        if item is not None:
            if self.manager and isinstance(item, (BaseValve, Switch)):
                self.manager.set_selected_explanation_item(item)
            self._show_menu(event, item)
        event.handled = True

    def show_menu(self, event):
        item = self._over_item(event)
        if item is not None:
            self.active_item = item
            if self.manager and isinstance(item, (BaseValve, Switch)):
                self.manager.set_active_canvas_item(item)
                self.manager.set_selected_explanation_item(item)
            self._show_menu(event, item)
        event.handled = True

    def select_left_down(self, event) -> None:
        """ """

        def set_state(state):
            ok, change = True, True
            if self.manager is not None:
                mode = "normal"
                if event.shift_down:
                    mode = "shift_select"

                if state:
                    func = self.manager.open_valve
                else:
                    func = self.manager.close_valve

                args = func(item.name, mode=mode)
                if args:
                    ok, change = args

            return ok, change

        event.handled = True

        item = self.active_item
        if item is None:
            return

        if self.manager and isinstance(item, (BaseValve, Switch)):
            self.manager.set_selected_explanation_item(item)

        if self.edit_mode:
            if event.shift_down:
                self._toggle_item_selection(item)
                return

            self.event_state = "drag"
            event.window.set_pointer(self.drag_pointer)
            return

        if isinstance(item, Laser):
            self._toggle_laser_state(item)
            return

        state = item.state
        nstate = not state
        if isinstance(item, Switch):
            set_state(nstate)

        else:
            if not isinstance(item, BaseValve):
                return

            if item.soft_lock:
                return

            # Use preview API for structured confirmation
            if self.manager and self.confirm_open and not isinstance(item, ManualSwitch):
                action = "open" if nstate else "close"
                preview_func = (
                    self.manager.preview_open_valve if nstate else self.manager.preview_close_valve
                )
                preview = preview_func(item.name)

                if not preview.allowed:
                    self._show_preview_dialog(preview)
                    return

                if preview.requires_confirmation or self.confirm_open:
                    if not self._show_preview_dialog(preview):
                        return

            ok, change = set_state(nstate)

        if ok:
            item.state = nstate

        if change and ok:
            self._select_hook(item)

        if change:
            self.invalidate_and_redraw()

        event.handled = True

    def _show_preview_dialog(self, preview):
        """Show structured preview dialog. Returns True if user confirms."""
        from pyface.api import confirm, YES

        lines = []
        action_label = "Open" if preview.requested_action == "open" else "Close"
        lines.append("{} valve {}?".format(action_label, preview.valve_name))
        lines.append("")

        if preview.current_state is not None:
            lines.append("Current state: {}".format("Open" if preview.current_state else "Closed"))

        if preview.owner:
            lines.append("Owner: {}".format(preview.owner))

        if preview.is_soft_locked:
            lines.append("WARNING: Software locked")

        if preview.interlocks:
            lines.append("Interlock present: {}".format(", ".join(preview.interlocks)))

        if preview.affected_children:
            lines.append("Also affects: {}".format(", ".join(preview.affected_children)))

        if preview.network_region_changes:
            for change in preview.network_region_changes:
                lines.append(change)

        if preview.reasons_blocking:
            lines.append("")
            lines.append("Blocked: {}".format("; ".join(preview.reasons_blocking)))

        msg = "\n".join(lines)

        if preview.warning_level == "error":
            title = "Actuation Blocked"
            from pyface.message_dialog import error

            error(None, msg, title=title)
            return False

        if preview.warning_level == "warning":
            title = "Actuation Warning"
        else:
            title = "Confirm Valve Action"

        result = confirm(None, msg, title=title)
        return result == YES

        item = self.active_item
        if item is None:
            return

        if self.manager and isinstance(item, (BaseValve, Switch)):
            self.manager.set_selected_explanation_item(item)

        if self.edit_mode:
            if event.shift_down:
                self._toggle_item_selection(item)
                return

            self.event_state = "drag"
            event.window.set_pointer(self.drag_pointer)
            return

        if isinstance(item, Laser):
            self._toggle_laser_state(item)
            return

        state = item.state
        nstate = not state
        if isinstance(item, Switch):
            set_state(nstate)

        else:
            if not isinstance(item, BaseValve):
                return

            if item.soft_lock:
                return

            if self.confirm_open:
                from pychron.core.ui.dialogs import myConfirmationDialog
                from pyface.api import NO

                if isinstance(item, ManualSwitch) or (isinstance(item, RoughValve) and not state):
                    msg = "Are you sure you want to {} {}".format(
                        "open" if not state else "close", item.name
                    )

                    dlg = myConfirmationDialog(
                        message=msg, title="Verfiy Valve Action", style="modal"
                    )
                    retval = dlg.open()
                    if retval == NO:
                        return

            ok, change = set_state(nstate)

        if ok:
            item.state = nstate

        if change and ok:
            self._select_hook(item)

        if change:
            self.invalidate_and_redraw()

        event.handled = True

    def edit_left_down(self, event):
        if event.shift_down:
            self._is_box_selecting = True
            self._box_start = self.map_data((event.x, event.y))
            self._box_end = self._box_start
            event.handled = True
            return

        item = self._over_item(event)
        if item is not None:
            self._toggle_item_selection(item)
        else:
            self.clear_selection()
        event.handled = True

    def edit_mouse_move(self, event):
        if self._is_box_selecting:
            self._box_end = self.map_data((event.x, event.y))
            self.invalidate_and_redraw()
        event.handled = True

    def edit_left_up(self, event):
        if self._is_box_selecting:
            self._is_box_selecting = False
            self._perform_box_select()
            self._box_start = None
            self._box_end = None
            self.invalidate_and_redraw()
        event.handled = True

    def _toggle_item_selection(self, item):
        if item in self.selected_items:
            self.selected_items.remove(item)
            item.selected = False
        else:
            self.selected_items.append(item)
            item.selected = True

    def clear_selection(self):
        for item in self.selected_items:
            item.selected = False
        self.selected_items = []

    def select_all(self):
        self.clear_selection()
        for item in self.scene.get_items():
            if isinstance(item, (BaseValve, Switch, Laser)):
                self.selected_items.append(item)
                item.selected = True
        self.invalidate_and_redraw()

    def _perform_box_select(self):
        if self._box_start is None or self._box_end is None:
            return

        x1 = min(self._box_start[0], self._box_end[0])
        x2 = max(self._box_start[0], self._box_end[0])
        y1 = min(self._box_start[1], self._box_end[1])
        y2 = max(self._box_start[1], self._box_end[1])

        if not event.shift_down:
            self.clear_selection()

        for item in self.scene.get_items():
            bx, by, bx2, by2 = item.get_bounds()
            if bx2 >= x1 and bx <= x2 and by2 >= y1 and by <= y2:
                if item not in self.selected_items:
                    self.selected_items.append(item)
                    item.selected = True
        self.invalidate_and_redraw()

    def drag_mouse_move(self, event):
        if not self.selected_items:
            self.selected_items = [self.active_item] if self.active_item else []

        dx, dy = self.map_data((event.x, event.y))

        for si in self.selected_items:
            w, h = si.width, si.height
            nx = dx - w / 2.0
            ny = dy - h / 2.0

            if self.snap_to_grid:
                nx, ny = snap_to_grid(nx, ny, interval=self.grid_interval)

            if event.shift_down:
                if self._px is not None and not self._constrain:
                    xx = abs(event.x - self._px)
                    yy = abs(event.y - self._py)
                    self._constrain = "v" if yy > xx else "h"
                else:
                    self._px = event.x
                    self._py = event.y
            else:
                self._constrain = False
                self._px, self._py = None, None

            if self._constrain == "h":
                si.x = nx
            elif self._constrain == "v":
                si.y = ny
            else:
                si.x, si.y = nx, ny

            si.request_layout()
        self.invalidate_and_redraw()

    def drag_left_up(self, event):
        self._set_normal_state(event)

    def drag_mouse_leave(self, event):
        self._set_normal_state(event)

    def on_lock(self):
        item = self._active_item
        if item:
            lock = not item.soft_lock
            self.manager.set_software_lock(item.name, lock)

    def on_force_close(self):
        self._force_actuate(self.manager.close_valve, False)

    def on_force_open(self):
        self._force_actuate(self.manager.open_valve, True)

    def iter_valves(self):
        return self.scene.valves.values()
        # return (i for i in six.itervalues(self.scene.valves))

    # private
    def _force_actuate(self, func, state):
        item = self._active_item
        if item:
            ok, change = func(item.name, mode="normal", force=True)
            if ok:
                item.state = state

            if change and ok:
                self._select_hook(item)

            if change:
                self.invalidate_and_redraw()

    def _set_normal_state(self, event):
        self.event_state = "normal"
        event.window.set_pointer(self.normal_pointer)

    def _select_hook(self, item):
        pass

    @on_trait_change("display_volume, volume_key")
    def _update_tool(self, name, new):
        self.tool.trait_set(**{name: new})

    def _toggle_laser_state(self, item):
        item.toggle_animate()
        self.request_redraw()

    def _reset_network_visualization(self) -> None:
        for item in self.scene.get_items():
            if hasattr(item, "active_color") and hasattr(item, "default_color"):
                item.active_color = item.default_color
            if hasattr(item, "oactive_color"):
                item.active_color = item.oactive_color

    def _get_switch_by_name(self, name):
        if self.scene and self.scene.valves:
            s = next((i for i in self.iter_valves() if i.name == name), None)
            # if s is None:
            #     names = [i.name for i in self.iter_valves()]
            #     print('No switch with name "{}". Names={}'.format(name, names))

            return s

    def _get_object_by_name(self, name):
        return self.scene.get_item(name)

    def _action_factory(self, name, func, klass=None, **kw):
        """ """
        if klass is None:
            klass = Action

        a = klass(name=name, on_perform=getattr(self, func), **kw)

        return a

    def _show_menu(self, event, obj):
        actions = []
        allow_locking = self.manager.mode != "client" or globalv.client_only_locking
        allow_force = self.manager.mode != "client" and self.force_actuate_enabled

        if allow_locking and isinstance(obj, BaseValve):
            t = "Lock"
            if obj.soft_lock:
                t = "Unlock"

            action = self._action_factory(t, "on_lock")
            actions.append(action)

        if allow_force:
            action = self._action_factory("Force Close", "on_force_close")
            actions.append(action)

            action = self._action_factory("Force Open", "on_force_open")
            actions.append(action)

        if actions:
            menu_manager = MenuManager(*actions)

            self._active_item = self.active_item
            control = event.window.control
            menu = menu_manager.create_menu(control, None)
            self._context_menu = menu

            global_pos = getattr(event, "global_pos", None)
            if global_pos is None and control is not None:
                size = control.size()
                global_pos = control.mapToGlobal(QPoint(int(event.x), int(size.height() - event.y)))

            if global_pos is not None and hasattr(menu, "exec_"):
                menu.exec_(global_pos)
            elif hasattr(menu, "exec_"):
                menu.exec_()
            else:
                menu.show()


# ============= EOF ====================================
