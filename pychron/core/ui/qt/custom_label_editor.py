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
from traits.api import (
    HasTraits,
    Str,
    Int,
    Button,
    Any,
    Instance,
    on_trait_change,
    Bool,
)
from traitsui.api import View, UItem, Color
from traitsui.basic_editor_factory import BasicEditorFactory
import re

from pyface.qt.QtGui import QLabel, QColor
from traitsui.qt.editor import Editor

# ============= standard library imports ========================
import random



# ============= local library imports  ==========================


class _CustomLabelEditor(Editor):
    color = Any
    bgcolor = Any
    weight = Any
    text_size = Any

    def init(self, parent):
        self.control = self._create_control(parent)
        #        self.item.on_trait_change(self._set_color, 'color')
        self.sync_value(self.factory.color, "color", mode="from")
        self.sync_value(self.factory.bgcolor, "bgcolor", mode="from")
        self.sync_value(self.factory.weight, "weight", mode="from")
        self.sync_value(self.factory.text_size, "text_size", mode="from")

    @on_trait_change("color, bgcolor, weight, text_size")
    def _update_style(self):
        self._set_style()

    def _set_style(
        self, control=None, color=None, bgcolor=None, size=None, weight=None
    ):
        if control is None:
            control = self.control

        if color is None:
            color = self.color

        if bgcolor is None:
            if self.bgcolor is None:
                bgcolor = "transparent"
            else:
                bgcolor = self.bgcolor

        if size is None:
            size = self.text_size
            if not size:
                size = self.item.size

        if weight is None:
            weight = self.weight
            if not weight:
                weight = self.item.weight

        color = self._qss_color(color)
        bgcolor = self._qss_color(bgcolor)

        css = """QLabel {{color:{};
        background-color:{};
        font-size:{}px;
        font-weight:{};}}
        """.format(
            color, bgcolor, size, weight
        )

        control.setStyleSheet(css)

    @staticmethod
    def _qss_color(value):
        """Return a Qt style sheet compatible color string.

        Accepts common Pychron/Traits representations:
        - 'red', '#RRGGBB', 'transparent', 'rgb(...)', 'rgba(...)'
        - '(r, g, b)' or '(r, g, b, a)' strings
        - (r, g, b) / (r, g, b, a) tuples/lists
        - QColor
        - QRgb/rgba integer
        """

        if value is None:
            return "transparent"

        if isinstance(value, str):
            s = value.strip()
            if not s:
                return "transparent"

            # Handle stringified tuples e.g. "(255, 0, 0, 255)"
            m = re.match(
                r"^[\(\[]\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)(?:\s*,\s*(\d+))?\s*[\)\]]$",
                s,
            )
            if m:
                r, g, b = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
                a = m.group(4)
                if a is None:
                    return f"rgb({r},{g},{b})"
                return f"rgba({r},{g},{b},{int(a)})"

            return s

        if isinstance(value, QColor):
            r, g, b, a = value.red(), value.green(), value.blue(), value.alpha()
            if a >= 255:
                return f"rgb({r},{g},{b})"
            return f"rgba({r},{g},{b},{a})"

        if isinstance(value, int):
            qc = QColor.fromRgba(value)
            r, g, b, a = qc.red(), qc.green(), qc.blue(), qc.alpha()
            if a >= 255:
                return f"rgb({r},{g},{b})"
            return f"rgba({r},{g},{b},{a})"

        if isinstance(value, (tuple, list)):
            if len(value) == 3:
                r, g, b = (int(value[0]), int(value[1]), int(value[2]))
                return f"rgb({r},{g},{b})"
            if len(value) == 4:
                r, g, b, a = (
                    int(value[0]),
                    int(value[1]),
                    int(value[2]),
                    int(value[3]),
                )
                if a >= 255:
                    return f"rgb({r},{g},{b})"
                return f"rgba({r},{g},{b},{a})"

        # TraitsUI Color or other objects often expose .name() (QColor-like)
        try:
            name = value.name()
        except Exception:
            name = None
        if name:
            return str(name)

        return str(value)

    # def update_editor(self):
    #     if self.control:
    #         if isinstance(self.value, (str, int, float, int, six.text_type)):
    #             self.control.setText(self.str_value)

    def _create_control(self, parent):
        control = QLabel()
        bgcolor = None
        if self.item.use_color_background:
            bgcolor = self.item.bgcolor
        self._set_style(color=self.item.color, bgcolor=bgcolor, control=control)

        control.setMargin(5)
        parent.setSpacing(0)

        return control


class CustomLabelEditor(BasicEditorFactory):
    klass = _CustomLabelEditor
    color = Str
    bgcolor = Str
    weight = Str
    text_size = Str


class CustomLabel(UItem):
    editor = Instance(CustomLabelEditor, ())
    size = Int(12)
    size_name = Str

    color = Color("black")
    color_name = Str

    bgcolor = Color("transparent")
    bgcolor_name = Str
    use_color_background = Bool(False)
    weight = Str("normal")

    # top_padding = Int(5)
    # bottom_padding = Int(5)
    # left_padding = Int(5)
    # right_padding = Int(5)

    def _size_name_changed(self):
        self.editor.text_size = self.size_name

    def _color_name_changed(self):
        self.editor.color = self.color_name

    def _bgcolor_name_changed(self):
        self.editor.bgcolor = self.bgcolor_name


# ===============================================================================
# demo
# ===============================================================================
class Demo(HasTraits):
    a = Str("asdfsdf")
    foo = Button
    color = Color("blue")
    bgcolor = Color("green")
    cnt = 0
    size = Int(12)

    def _foo_fired(self):
        self.a = "fffff {}".format(random.random())
        if self.cnt % 2 == 0:
            self.color = "red"
            self.bgcolor = "blue"
        else:
            self.bgcolor = "red"
            self.color = "blue"
        self.cnt += 1

    def traits_view(self):
        v = View(
            UItem("size"),
            "foo",
            CustomLabel(
                "a",
                #                             color='blue',
                size=24,
                size_name="size",
                #top_padding=10,
                #left_padding=10,
                color_name="color",
                bgcolor_name="bgcolor",
            ),
            resizable=True,
            width=400,
            height=100,
        )
        return v


if __name__ == "__main__":
    d = Demo()
    d.configure_traits()
    # ============= EOF =============================================
    #        css = '''QLabel {{ color:{}; font-size:{}px; font-weight:{};}}
    # # '''.format(self.item.color.name(), self.item.size, self.item.weight)
    #        control.setStyleSheet(css)

    #        control.setAlignment(Qt.AlignCenter)
    #        control.setGeometry(0, 0, self.item.width, self.item.height)
    #        vbox = QVBoxLayout()
    #        vbox.setSpacing(0)

    #        hbox = QHBoxLayout()

    #        hbox.addLayout(vbox)
    #        parent.addLayout(vbox)
    #        print vbox.getContentsMargins()
    #        vbox.setContentsMargins(5, 5, 5, 5)
    #        vbox.setSpacing(-1)
    #        vbox.addSpacing(5)
    #        vbox.addSpacing(10)
    #        vbox.addWidget(control)
    #        vbox.addSpacing(5)
    #        vbox.addStretch()

    #        vbox.setSpacing(-1)
    #        vbox.setMargin(10)
    #        control.setLayout(vbox)
    #        parent.addWidget(control)
