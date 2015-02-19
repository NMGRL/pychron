# ===============================================================================
# Copyright 2015 Jake Ross
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
from chaco.axis_view import float_or_auto
from enable.base_tool import BaseTool
from traits.api import HasTraits, Str, Int, Bool, Any, Float, Property, on_trait_change
from traitsui.api import View, UItem, Item, HGroup, VGroup, Group, TextEditor
# ============= standard library imports ========================
# ============= local library imports  ==========================

AxisView = View(VGroup(
    Group(
        Item("object.mapper.range.low", label="Low Range"),
        Item("object.mapper.range.high", label="High Range")),
    Group(
        Item("title", label="Title", editor=TextEditor()),
        Item("title_font", label="Font", style="simple"),
        Item("title_color", label="Color", style="custom"),
        Item("tick_interval", label="Interval", editor=TextEditor(evaluate=float_or_auto)),
        show_border=True,
        label="Main"),
    Group(
        Item("tick_color", label="Color", style="custom"),
        # editor=EnableRGBAColorEditor()),
        Item("tick_weight", label="Thickness"),
        # Item("tick_label_font", label="Font"),
        Item("tick_label_color", label="Label color", style="custom"),
        # editor=EnableRGBAColorEditor()),
        HGroup(
            Item("tick_in", label="Tick in"),
            Item("tick_out", label="Tick out"),
        ),
        Item("tick_visible", label="Visible"),
        show_border=True,
        label="Ticks"),
    Group(
        Item("axis_line_color", label="Color", style="custom"),
        # editor=EnableRGBAColorEditor()),
        Item("axis_line_weight", label="Thickness"),
        Item("axis_line_visible", label="Visible"),
        show_border=True,
        label="Line")),
    title='Edit Axis',
    x=50,
    y=50,
    buttons=["OK",])


class AxisTool(BaseTool):
    def normal_right_down(self, event):
        if self.hittest(event):
            self.component.edit_traits(view=AxisView, kind='live')
            self.component.request_redraw()
            event.handled = True

    @on_trait_change('component.+')
    def handle_change(self, name, new):
        if name.startswith('_'):
            return
        self.component.request_redraw()

    def hittest(self, event):
        return self.component.is_in(event.x, event.y)

# ============= EOF =============================================



