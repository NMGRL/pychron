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
from traits.api import Int
# ============= standard library imports ========================
# ============= local library imports  ==========================
from PySide.QtGui import QFrame, QPainter, QColor
from traitsui.basic_editor_factory import BasicEditorFactory
from traitsui.qt4.editor import Editor

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
            self.value = v
            self.update()

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
