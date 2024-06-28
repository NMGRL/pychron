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

from enable.enable_traits import Pointer
from pyface.action.menu_manager import MenuManager
from pyface.qt.QtGui import QToolTip
from traits.api import Any, Str, on_trait_change, Bool, List
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


class ExtractionLineCanvas2D(SceneCanvas):
    """ """

    scene_klass = ExtractionLineScene

    use_backbuffer = True
    border_visible = False
    active_item = Any

    selected_id = Str
    show_axes = False
    show_grids = False
    use_zoom = False
    use_pan = False
    padding_left = 0
    padding_right = 0
    padding_bottom = 0
    padding_top = 0

    manager = Any

    aspect_ratio = 4 / 3.0

    y_range = (-10, 25)

    display_volume = Bool
    volume_key = Str
    confirm_open = Bool(True)

    force_actuate_enabled = True

    drag_pointer = Pointer("bullseye")
    snap_to_grid = True
    grid_interval = 0.5
    edit_mode = Bool(False)
    _constrain = False

    _px = None
    _py = None

    def __init__(self, *args, **kw):
        super(ExtractionLineCanvas2D, self).__init__(*args, **kw)

        tool = ExtractionLineInfoTool(
            scene=self.scene, manager=self.manager, component=self
        )
        overlay = ExtractionLineInfoOverlay(tool=tool, component=self)
        self.tool = tool
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
            switch.state = nstate
            if refresh:
                self.invalidate_and_redraw()

    def update_switch_owned_state(self, name, owned):
        switch = self._get_switch_by_name(name)
        if switch is not None:
            switch.owned = owned

            self.invalidate_and_redraw()

    def update_switch_lock_state(self, name, lockstate):
        switch = self._get_switch_by_name(name)
        if switch is not None:
            switch.soft_lock = lockstate
            self.invalidate_and_redraw()

    def load_canvas_file(
        self, canvas_path=None, canvas_config_path=None, valves_path=None
    ):
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
        return self.scene.get_is_in(
            x, y, exclude=[BorderLine, Elbow, Connection, Fork, Cross, Tee]
        )

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
            if isinstance(item, (BaseValve, Switch)):
                event.window.set_pointer(self.select_pointer)
                if self.manager:
                    self.manager.set_selected_explanation_item(item)
        else:
            event.window.control.setToolTip("")
            QToolTip.hideText()

            self.active_item = None
            self.event_state = "normal"
            event.window.set_pointer(self.normal_pointer)
            if self.manager:
                self.manager.set_selected_explanation_item(None)

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
            self._show_menu(event, item)
        event.handled = True

    def select_left_down(self, event):
        """ """

        def set_state(state):
            ok, change = True, True
            if self.manager is not None:
                mode = "normal"
                if event.shift_down:
                    mode = "shift_select"

                if state:
                    # ok, change = self.manager.open_valve(item.name, mode=mode)
                    func = self.manager.open_valve
                else:
                    # ok, change = self.manager.close_valve(item.name, mode=mode)
                    func = self.manager.close_valve

                args = func(item.name, mode=mode)
                if args:
                    ok, change = args

            return ok, change

        event.handled = True

        item = self.active_item
        if item is None:
            return

        if self.edit_mode:
            self.event_state = "drag"
            event.window.set_pointer(self.drag_pointer)
            return

        if isinstance(item, Laser):
            self._toggle_laser_state(item)
            return

        state = item.state
        nstate = not state
        if isinstance(item, Switch):
            # mode = "normal"
            # # try:
            # if state:
            #     ok, change = self.manager.open_valve(item.name, mode=mode)
            # else:
            #     ok, change = self.manager.close_valve(item.name, mode=mode)
            #     # except TypeError, e:
            #     # ok, change = True, True
            set_state(nstate)

        else:
            if not isinstance(item, BaseValve):
                return

            if item.soft_lock:
                return

            if self.confirm_open:
                from pychron.core.ui.dialogs import myConfirmationDialog
                from pyface.api import NO

                if isinstance(item, ManualSwitch) or (
                    isinstance(item, RoughValve) and not state
                ):
                    msg = "Are you sure you want to {} {}".format(
                        "open" if not state else "close", item.name
                    )
                    # event.handled = True

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

    def drag_mouse_move(self, event):
        si = self.active_item

        x, y = event.x, event.y
        dx, dy = self.map_data((x, y))
        w, h = si.width, si.height

        dx -= w / 2.0
        dy -= h / 2.0

        if self.snap_to_grid:
            dx, dy = snap_to_grid(dx, dy, interval=self.grid_interval)

        if event.shift_down:
            if self._px is not None and not self._constrain:
                xx = abs(x - self._px)
                yy = abs(y - self._py)
                self._constrain = "v" if yy > xx else "h"
            else:
                self._px = x
                self._py = y
        else:
            self._constrain = False
            self._px, self._py = None, None

        if self._constrain == "h":
            si.x = dx
        elif self._constrain == "v":
            si.y = dy
        else:
            si.x, si.y = dx, dy

        si.request_layout()
        self.invalidate_and_redraw()

    def drag_left_up(self, event):
        self._set_normal_state(event)

    def drag_mouse_leave(self, event):
        self._set_normal_state(event)

    def on_lock(self):
        item = self._active_item
        if item:
            item.soft_lock = lock = not item.soft_lock
            self.manager.set_software_lock(item.name, lock)
            self.request_redraw()

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

        if self.manager.mode != "client" or not globalv.client_only_locking:
            # print self.active_item, isinstance(self.active_item, Switch)
            # if isinstance(self.active_item, Switch):
            if isinstance(self.active_item, BaseValve):
                t = "Lock"
                if obj.soft_lock:
                    t = "Unlock"

                action = self._action_factory(t, "on_lock")
                actions.append(action)

            if self.force_actuate_enabled:
                action = self._action_factory("Force Close", "on_force_close")
                actions.append(action)

                action = self._action_factory("Force Open", "on_force_open")
                actions.append(action)

        if actions:
            menu_manager = MenuManager(*actions)

            self._active_item = self.active_item
            menu = menu_manager.create_menu(event.window.control, None)
            menu.show()


# ============= EOF ====================================
