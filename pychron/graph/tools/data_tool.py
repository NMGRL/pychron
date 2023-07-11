# ===============================================================================
# Copyright 2012 Jake Ross
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
from __future__ import absolute_import

# ============= standard library imports ========================
from datetime import datetime

from chaco.api import TextBoxOverlay
from enable.base_tool import BaseTool, KeySpec
from traits.api import Event, Any, Enum, Tuple, Bool, Int


# ============= local library imports  ==========================


class DataTool(BaseTool):
    new_value = Event
    last_mouse_position = Tuple
    visible = Bool(True)
    inspector_key = KeySpec("i")
    parent = Any
    plot = Any
    plotid = Int
    use_date_str = True
    normalize_time = False
    x_format = "{:0.2f}"
    predict_value_func = None
    filter_components = True

    def normal_key_pressed(self, event):
        if self.inspector_key.match(event):
            self.visible = not self.visible
            event.handled = True

    def normal_mouse_move(self, event):
        comp = self.component
        plot = self.plot
        if comp is not None:
            d = dict()

            x, y = comp.map_data([event.x, event.y])
            if self.filter_components:
                comps = comp.container.components_at(event.x, event.y)
                if comp not in comps:
                    self.new_value = d
                    return

            ind = plot.index.metadata.get("hover")
            if ind is not None:
                y = plot.value.get_data()[ind][0]
                x = plot.index.get_data()[ind][0]

            d["text"] = self._make_text(plot, x, y)
            self.new_value = d
            self.last_mouse_position = (event.x, event.y)

    def _make_text(self, plot, x, y):
        if self.normalize_time:
            try:
                sx = plot.index.get_data()[0]
                x -= sx
            except IndexError:
                return

        if self.use_date_str:
            # convert timestamp to str
            date = datetime.fromtimestamp(x)
            xi = date.strftime("%d/%m %H:%M:%S")
        else:
            try:
                xi = self.x_format.format(x)
            except ValueError:
                xi = ""

        ret = "{},{:0.3f}".format(xi, y)
        if self.predict_value_func:
            ret = "{},{}".format(ret, self.predict_value_func(x, y))
        return ret


class DataToolOverlay(TextBoxOverlay):
    border_visible = True
    bgcolor = "orange"
    tool = Any
    visibility = Enum("auto", True, False)
    visible = False
    # font = "modern 12"
    tooltip_mode = Bool(False)

    def _tool_changed(self, old, new):
        if old:
            old.on_trait_event(self._new_value_updated, "new_value", remove=True)
            old.on_trait_change(self._tool_visible_changed, "visible", remove=True)
        if new:
            new.on_trait_event(self._new_value_updated, "new_value")
            new.on_trait_change(self._tool_visible_changed, "visible")
            self._tool_visible_changed()

    def _new_value_updated(self, event):
        if event is None:
            self.text = ""
            if self.visibility == "auto":
                self.visible = False
            return
        elif self.visibility == "auto":
            self.visible = True

        if self.tooltip_mode:
            self.alternate_position = self.tool.last_mouse_position
        else:
            self.alternate_position = None

        txt = event.get("text", "")
        if txt is not None:
            self.text = txt
        self.component.request_redraw()

    def _visible_changed(self):
        self.component.request_redraw()

    def _tool_visible_changed(self):
        self.visibility = self.tool.visible
        if self.visibility != "auto":
            self.visible = self.visibility


# ============= EOF =============================================
