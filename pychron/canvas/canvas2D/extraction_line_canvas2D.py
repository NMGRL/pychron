# ===============================================================================
# Copyright 2011 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================

# ============= enthought library imports =======================
from traits.api import Any, Str, on_trait_change, Bool
from pyface.action.menu_manager import MenuManager
from traitsui.menu import Action
from pyface.qt.QtGui import QToolTip

# ============= standard library imports ========================`
import os
# ============= local library imports  ==========================
from pychron.canvas.canvas2D.overlays.extraction_line_overlay import ExtractionLineInfoTool, ExtractionLineInfoOverlay
from pychron.canvas.canvas2D.scene.primitives.primitives import BorderLine
from pychron.canvas.scene_viewer import SceneCanvas
from pychron.canvas.canvas2D.scene.extraction_line_scene import ExtractionLineScene
from pychron.canvas.canvas2D.scene.primitives.valves import RoughValve, \
    BaseValve
import weakref

W = 2
H = 2


class ExtractionLineAction(Action):
    chamber = Str


class ExtractionLineCanvas2D(SceneCanvas):
    """
    """
    use_backbuffer = True
    border_visible = False
    #     valves = Dict
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

    aspect_ratio = 4 / 3.

    y_range = (-10, 25)

    display_volume = Bool
    volume_key = Str
    confirm_open = Bool(True)

    def __init__(self, *args, **kw):
        super(ExtractionLineCanvas2D, self).__init__(*args, **kw)

        tool = ExtractionLineInfoTool(scene=self.scene,
                                      manager=self.manager)
        overlay = ExtractionLineInfoOverlay(tool=tool,
                                            component=self)
        self.tool = tool
        self.tools.append(tool)
        self.overlays.append(overlay)

    def toggle_item_identify(self, name):
        v = self._get_valve_by_name(name)
        if v is not None:
            try:
                v.identify = not v.identify
            except AttributeError:
                pass

    def update_valve_state(self, name, nstate, refresh=True, mode=None):
        """
        """
        valve = self._get_valve_by_name(name)
        if valve is not None:
            valve.state = nstate
        self.draw_valid = False

    def update_valve_owned_state(self, name, owned):
        valve = self._get_valve_by_name(name)
        if valve is not None:
            valve.owned = owned
        self.draw_valid = False

    def update_valve_lock_state(self, name, lockstate):
        valve = self._get_valve_by_name(name)
        if valve is not None:
            valve.soft_lock = lockstate
            # self.request_redraw()
        self.draw_valid = False

    # def load_canvas_file(self, cname, setup_name='canvas', valve_name='valves'):
    #
    #     p = os.path.join(paths.canvas2D_dir, '{}.xml'.format(setup_name))
    #     p2 = os.path.join(paths.canvas2D_dir, cname)
    #     p3 = os.path.join(paths.extraction_line_dir, '{}.xml'.format(valve_name))
    #     if os.path.isfile(p):
    #         self.scene.load(p, p2, p3, self)

    def load_canvas_file(self, canvas_path=None, canvas_config_path=None, valves_path=None):
        if canvas_path is None:
            canvas_path = self.manager.application.preferences.get('pychron.extraction_line.canvas_path')
        if canvas_config_path is None:
            canvas_config_path = self.manager.application.preferences.get('pychron.extraction_line.canvas_config_path')
        if valves_path is None:
            valves_path = self.manager.application.preferences.get('pychron.extraction_line.valves_path')

        if os.path.isfile(canvas_path):
            self.scene.load(canvas_path, canvas_config_path, valves_path, weakref.ref(self)())

    def _over_item(self, event):
        x, y = event.x, event.y
        return self.scene.get_is_in(x, y, exclude=[BorderLine, ])

    def normal_left_down(self, event):
        pass

    def normal_mouse_move(self, event):

        item = self._over_item(event)
        if item is not None:
            self.event_state = 'select'
            if item != self.active_item:
                self.active_item = item
            if isinstance(item, BaseValve):
                event.window.set_pointer(self.select_pointer)
                if self.manager:
                    self.manager.set_selected_explanation_item(item)
        else:
            event.window.control.setToolTip('')
            QToolTip.hideText()

            self.active_item = None
            self.event_state = 'normal'
            event.window.set_pointer(self.normal_pointer)
            if self.manager:
                self.manager.set_selected_explanation_item(None)

    def select_mouse_move(self, event):
        """
        """
        ctrl = event.window.control
        try:
            tt = self.active_item.get_tooltip_text()
            ctrl.setToolTip(tt)
        except AttributeError:
            pass
        self.normal_mouse_move(event)

    def select_right_down(self, event):
        item = self.active_item

        if item is not None:
            self._show_menu(event, item)
        event.handled = True

    def select_left_down(self, event):
        """

        """
        item = self.active_item
        if item is None:
            return

        if not isinstance(item, BaseValve):
            return

        if item.soft_lock:
            return

        state = item.state

        if self.confirm_open and isinstance(item, RoughValve) and not state:
            event.handled = True

            from pychron.core.ui.dialogs import myConfirmationDialog
            from pyface.api import NO

            dlg = myConfirmationDialog(
                message='Are you sure you want to open {}'.format(item.name),
                title='Verfiy Valve Action',
                style='modal')
            retval = dlg.open()
            if retval == NO:
                return

        state = not state

        change = False
        if self.manager is not None:
            mode = 'normal'
            if event.shift_down:
                mode = 'shift_select'

            if state:
                ok, change = self.manager.open_valve(item.name, mode=mode)
            else:
                ok, change = self.manager.close_valve(item.name, mode=mode)
        else:
            ok = True

        if ok and not item.soft_lock:
            item.state = state

        if change:
            self.request_redraw()

    def on_lock(self):
        item = self._active_item
        if item:
            item.soft_lock = lock = not item.soft_lock
            self.manager.set_software_lock(item.name, lock)
            self.request_redraw()

    # def OnSample(self):
    # pass
    #
    # def OnCycle(self):
    #     pass
    #
    # def OnProperties(self, event):
    #     self.manager.show_valve_properties(self.active_item.name)

    def iter_valves(self):
        return (i for i in self.scene.valves.itervalues() if isinstance(i, BaseValve))

    def _get_valve_by_name(self, name):
        return next((i for i in self.scene.valves.itervalues()
                     if isinstance(i, BaseValve) and i.name == name), None)

    def _get_object_by_name(self, name):
        return self.scene.get_item(name)

    def _action_factory(self, name, func, klass=None, **kw):
        """
        """
        if klass is None:
            klass = Action

        a = klass(name=name,
                  on_perform=getattr(self, func), **kw)

        return a

    def _show_menu(self, event, obj):
        actions = []
        if self.manager.mode != 'client':
            if isinstance(self.active_item, BaseValve):
                t = 'Lock'
                if obj.soft_lock:
                    t = 'Unlock'

                action = self._action_factory(t, 'on_lock')
                actions.append(action)

        if actions:
            menu_manager = MenuManager(*actions)

            self._active_item = self.active_item
            menu = menu_manager.create_menu(event.window.control, None)
            menu.show()

    @on_trait_change('display_volume, volume_key')
    def _update_tool(self, name, new):
        self.tool.trait_set(**{name: new})

    def _scene_default(self):
        s = ExtractionLineScene(canvas=weakref.ref(self)())
        return s


# ============= EOF ====================================
