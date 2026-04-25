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
from __future__ import annotations

import random
import re

from traits.api import Bool, Button, HasTraits, Instance, Int, Str, on_trait_change, Any
from traitsui.api import Color, UItem, View
from traitsui.basic_editor_factory import BasicEditorFactory
from traitsui.qt.editor import Editor

from pyface.qt.QtGui import QColor, QLabel


class _CustomLabelEditor(Editor):
    """Qt editor for CustomLabel trait items."""

    color = Color
    bgcolor = Color("transparent")
    weight = Str
    text_size = Int

    def init(self, parent: Any) -> None:
        """Initialize the editor and set up trait synchronization."""
        self.control = self._create_control(parent)
        #        self.item.on_trait_change(self._set_color, 'color')
        self.sync_value(self.factory.color, "color", mode="from")
        self.sync_value(self.factory.bgcolor, "bgcolor", mode="from")
        self.sync_value(self.factory.weight, "weight", mode="from")
        self.sync_value(self.factory.text_size, "text_size", mode="from")

    @on_trait_change("color, bgcolor, weight, text_size")
    def _update_style(self) -> None:
        """Update the label style when any styling trait changes."""
        self._set_style()

    def _set_style(
        self,
        control: Any = None,
        color: Any = None,
        bgcolor: Any = None,
        size: Any = None,
        weight: Any = None,
    ) -> None:
        """Apply stylesheet to the control based on styling traits."""
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

        border_str = self.item.border_style
        border_radius = self.item.border_radius

        color = self._qss_color(color)
        bgcolor = self._qss_color(bgcolor)

        css = f"""QLabel {{color:{color};
        background-color:{bgcolor};
        font-size:{size}px;
        font-weight:{weight};
        border: {border_str};
        border-radius: {border_radius};
        }}
        """

        control.setStyleSheet(css)

    @staticmethod
    def _qss_color(value: Any) -> str:
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

    def _create_control(self, parent: Any) -> QLabel:
        """Create and initialize the QLabel control."""
        control = QLabel()
        bgcolor = None
        if self.item.use_color_background:
            bgcolor = self.item.bgcolor
        self._set_style(color=self.item.color, bgcolor=bgcolor, control=control)

        control.setMargin(5)
        parent.setSpacing(0)

        return control


class CustomLabelEditor(BasicEditorFactory):
    """Factory for _CustomLabelEditor."""

    klass = _CustomLabelEditor
    color = Str
    bgcolor = Str("transparent")
    weight = Str
    text_size = Str


class CustomLabel(UItem):
    """TraitsUI item for stylable read-only text display."""

    editor = Instance(CustomLabelEditor, ())
    size = Int(12)
    size_name = Str

    color = Color("black")
    color_name = Str

    bgcolor = Color("transparent")
    bgcolor_name = Str
    use_color_background = Bool(False)
    weight = Str("normal")
    border_style = Str("0px solid black")
    border_radius = Str("0px")

    def _size_name_changed(self) -> None:
        """Update editor when dynamic size trait name changes."""
        self.editor.text_size = self.size_name

    def _color_name_changed(self) -> None:
        """Update editor when dynamic color trait name changes."""
        self.editor.color = self.color_name

    @on_trait_change("bgcolor")
    def _bgcolor_changed(self) -> None:
        """Automatically enable background color when bgcolor is set."""
        if self.bgcolor != Color("transparent"):
            self.use_color_background = True

    def _bgcolor_name_changed(self) -> None:
        """Update editor when dynamic background color trait name changes."""
        self.editor.bgcolor = self.bgcolor_name


# ===============================================================================
# Demo
# ===============================================================================
class Demo(HasTraits):
    """Demo class for testing CustomLabel."""

    a = Str("")
    foo = Button
    color = Color("blue")
    bgcolor = Color("#eaebbc")
    cnt = 0
    size = Int(12)

    def _foo_fired(self) -> None:
        """Toggle colors when foo button is fired."""
        self.a = "fffff {}".format(random.random())
        if self.cnt % 2 == 0:
            self.color = "red"
            self.bgcolor = "blue"
        else:
            self.bgcolor = "red"
            self.color = "blue"
        self.cnt += 1

    def traits_view(self) -> View:
        """Return the traits view for the demo."""
        v = View(
            UItem("size"),
            "foo",
            CustomLabel(
                "a",
                size=24,
                size_name="size",
                color_name="color",
                bgcolor_name="bgcolor",
                border_style="2px solid orange",
                border_radius="5px",
            ),
            resizable=True,
            width=400,
            height=100,
        )
        return v


if __name__ == "__main__":
    d = Demo()
    d.configure_traits()
