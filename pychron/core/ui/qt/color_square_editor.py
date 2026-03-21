# ===============================================================================
# Copyright 2013 Jake Ross
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
from traits.api import Int

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pyface.qt.QtGui import QFrame, QPainter, QColor
from traitsui.basic_editor_factory import BasicEditorFactory
from traitsui.qt.editor import Editor


class Square(QFrame):
    value = None
    width = 10
    height = 10

    def __init__(self):
        self.value = QColor(0, 0, 0)
        super(Square, self).__init__()

    #        super(Bar, self).__init__()
    #        self._cmap = get_cmap('jet')

    def paintEvent(self, e):
        qp = QPainter()
        qp.begin(self)
        qp.setBrush(self.value)
        qp.drawRect(0, 5, self.width, self.height)
        qp.end()

    def set_value(self, v):
        if v is not None:
            self.value = self._coerce_qcolor(v)
            self.update()

    def _coerce_qcolor(self, color):
        if isinstance(color, QColor):
            return color
        if hasattr(color, "rgba"):
            rgba = color.rgba
            if len(rgba) == 4:
                return QColor.fromRgbF(*rgba)
        if isinstance(color, str):
            if color.startswith("0x"):
                try:
                    color = int(color, 16)
                except ValueError:
                    return QColor(color)
            else:
                return QColor(color)
        if isinstance(color, int):
            return QColor((color >> 16) & 255, (color >> 8) & 255, color & 255)
        if isinstance(color, (tuple, list)):
            if len(color) == 3:
                r, g, b = color
                a = 1.0
            elif len(color) == 4:
                r, g, b, a = color
            else:
                return QColor(color)
            if all(isinstance(v, float) for v in (r, g, b, a)) and max(
                r, g, b, a
            ) <= 1.0:
                return QColor.fromRgbF(r, g, b, a)
            if a <= 1.0:
                a = int(round(a * 255))
            return QColor(int(r), int(g), int(b), int(a))
        return QColor(color)


class _ColorSquareEditor(Editor):
    def init(self, parent):
        self.control = Square()

    def update_editor(self):
        if self.control:
            self.control.set_value(self.value)


class ColorSquareEditor(BasicEditorFactory):
    klass = _ColorSquareEditor
    width = Int(100)


# ============= EOF =============================================
