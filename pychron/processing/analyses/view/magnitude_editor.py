# ===============================================================================
# Copyright 2014 Jake Ross
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

#============= enthought library imports =======================
from pyface.qt import QtCore, QtGui

#============= standard library imports ========================
#============= local library imports  ==========================
from traitsui.qt4.table_editor import TableDelegate
from traitsui.table_column import ObjectColumn


# class Bar(QtGui.QFrame):
#     bar_width = 10
#
#     def paintEvent(self, evt):
#         qp = QtGui.QPainter()
#         qp.begin(self)
#         # qp.setBrush(QtGui.QColor(*self.value))
#         qp.drawRect(0, 0, self.bar_width, 20)
#         qp.end()

#
# class _MagnitudeEditor(Editor):
#     def init(self, parent):
#         self.control = Bar()
#
#     def update_editor(self):
#         if self.control:
#             self.control.bar_width = self.value
#
#
# class MagnitudeEditor(BasicEditorFactory):
#     klass = _MagnitudeEditor

class MagnitudeRenderer(TableDelegate):
    bar_width = 50

    def editorEvent(self, event, model, option, index):
        pass

    def paint(self, painter, option, index):
        column = index.model()._editor.columns[index.column()]
        obj = index.data(QtCore.Qt.UserRole)
        v = column.get_raw_value(obj)

        painter.save()
        # painter.begin(self)
        # qp.setBrush(QtGui.QColor(*self.value))
        brush = QtGui.QBrush(QtCore.Qt.SolidPattern)
        brush.setColor(QtGui.QColor(255, 0, 0))
        rect = option.rect
        w = rect.width()
        rect.setWidth(w * v * 0.01)
        painter.fillRect(rect,
                         brush)
        painter.restore()


class MagnitudeColumn(ObjectColumn):
    def __init__(self, **traits):
        """ Initializes the object.
        """
        super(MagnitudeColumn, self).__init__(**traits)

        # force the renderer to be a checkbox renderer
        self.renderer = MagnitudeRenderer()

# ============= EOF =============================================

