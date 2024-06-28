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
from chaco.axis import DEFAULT_TICK_FORMATTER
from chaco.axis_view import float_or_auto
from enable.base_tool import BaseTool
from traits.api import on_trait_change, HasTraits, Font, Str
from traitsui.api import View, Item, HGroup, VGroup, TextEditor, Handler

# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.editors.api import FontEditor

limit_grp = VGroup(
    Item(
        "object.mapper.range.high",
        label="Upper",
        springy=True,
        editor=TextEditor(enter_set=True, auto_set=False),
    ),
    Item(
        "object.mapper.range.low",
        label="Lower",
        springy=True,
        editor=TextEditor(enter_set=True, auto_set=False),
    ),
    show_border=True,
    label="Limits",
)

title_grp = VGroup(
    Item("title", label="Title", editor=TextEditor()),
    Item("wrapper.title_font", label="Font", editor=FontEditor()),
    Item("title_color", label="Color"),
    show_border=True,
    label="Title",
)
tick_grp = VGroup(
    Item("tick_color", label="Color"),
    # editor=EnableRGBAColorEditor()),
    Item("tick_weight", label="Thickness"),
    # Item('tick_label_font', label='Font'),
    Item("tick_label_color", label="Label color"),
    # editor=EnableRGBAColorEditor()),
    HGroup(Item("tick_in", label="Tick in"), Item("tick_out", label="Tick out")),
    Item("tick_visible", label="Visible"),
    Item("tick_interval", label="Interval", editor=TextEditor(evaluate=float_or_auto)),
    Item(
        "wrapper.tick_label_format_str",
        tooltip="Enter a formatting string to apply to the tick labels. Currently the only supported "
        "option is to enter a number from 0-9 specifying the number of decimal places",
        label="Format",
    ),
    show_border=True,
    label="Ticks",
)
line_grp = VGroup(
    Item("axis_line_color", label="Color"),
    # editor=EnableRGBAColorEditor()),
    Item("axis_line_weight", label="Thickness"),
    Item("axis_line_visible", label="Visible"),
    show_border=True,
    label="Line",
)

AxisView = View(
    VGroup(limit_grp, title_grp, tick_grp, line_grp),
    title="Edit Axis",
    x=50,
    y=50,
    buttons=[
        "OK",
    ],
)


class AxisViewHandler(Handler):
    def init(self, info):
        from pyface.qt import QtCore

        info.ui.control.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        return True


class WrapAxis(HasTraits):
    title_font = Font
    tick_label_format_str = Str(enter_set=True, auto_set=False)

    def __init__(self, comp, *args, **kw):
        super(WrapAxis, self).__init__(*args, **kw)
        self._comp = comp
        self.title_font = str(comp.title_font)
        self.on_trait_change(self._update_title_font, "title_font")

    @on_trait_change("tick_label_format_str")
    def handle_change(self, new):
        func = DEFAULT_TICK_FORMATTER
        if new.isdigit():
            f = "{{:0.{}f}}".format(new)

            def func(x):
                return f.format(x)

        self._comp.tick_label_formatter = func

    def _update_title_font(self, *args, **kw):
        self._comp.title_font = str(self.title_font)
        self._comp.request_redraw()

    def trait_context(self):
        return {"object": self._comp, "wrapper": self}


class AxisTool(BaseTool):
    def normal_right_down(self, event):
        if self.hittest(event):
            wrap_axis = WrapAxis(self.component)

            wrap_axis.edit_traits(view=AxisView, handler=AxisViewHandler(), kind="live")
            self.component.request_redraw()
            event.handled = True

    @on_trait_change("component:+")
    def handle_change(self, name, new):
        if name.startswith("_"):
            return
        self.component.request_redraw()

    def hittest(self, event):
        return self.component.is_in(event.x, event.y)


# ============= EOF =============================================
