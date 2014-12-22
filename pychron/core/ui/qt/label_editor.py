# ===============================================================================
# Copyright 2014 Jake Ross
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
from PySide import QtCore
from PySide.QtGui import QLabel, QPainter, QColor, QWidget, QHBoxLayout
from traits.api import Str
from traits.trait_types import Event
# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.qt4.basic_editor_factory import BasicEditorFactory
from traitsui.qt4.editor import Editor


class mLabel(QLabel):
    color = ''
    # text = ''
    # def __init__(self, text):
    # super(mLabel, self).__init__()
    # self.text= text

    def paintEvent(self, evt):
        # print 'paint', self.color, self.text(), self.width(), self.height(), evt.rect().width()
        qp = QPainter()
        qp.begin(self)
        qp.setBrush(QColor('#{}'.format(self.color[:-2])))
        qp.drawRect(0, 0, self.width(), self.height())
        qp.end()

        qp.begin(self)
        qp.setPen(self._get_text_color())
        qp.drawText(evt.rect(), QtCore.Qt.AlignCenter, self.text())
        qp.end()

    def _get_text_color(self):
        r = self.color[:2]
        g = self.color[2:4]
        b = self.color[4:6]
        s = sum((int(r, 16), int(g, 16), int(b, 16)))
        c = 'white' if s < 256 else 'black'
        return QColor(c)

        # super(mLabel, self).paintEvent(evt)


class _LabelWidget(QWidget):
    # def __init__(self):
    #     super(_LabelWidget, self).__init__()

    def build(self, labels):
        self._dispose_items()
        layout = self.layout()
        for li in labels:
            l = mLabel(li.text)
            l.color = li.color
            layout.addWidget(l)

        self.update()

    def _dispose_items(self):
        """ Disposes of each current list item.
        """
        layout = self.layout()
        if not layout:
            layout = QHBoxLayout()
            layout.setSpacing(10)
            self.setLayout(layout)
            return

        child = layout.takeAt(0)
        while child is not None:
            control = child.widget()
            if control is not None:
                control.deleteLater()
            child = layout.takeAt(0)
        del child


class _LabelEditor(Editor):
    refresh = Event

    def init(self, parent):
        self.control = _LabelWidget()
        self.sync_value(self.factory.refresh, 'refresh')

        extended_name = self.extended_name.replace('.', ':')
        self.context_object.on_trait_change(self.update_editor,
                                            extended_name + '_items?', dispatch='ui')

    def update_editor(self):
        self.control.blockSignals(True)
        self.control.build(self.value)
        self.control.blockSignals(False)

    def _refresh_fired(self):
        self.update_editor()


class LabelEditor(BasicEditorFactory):
    klass = _LabelEditor
    refresh = Str


# ============= EOF =============================================



