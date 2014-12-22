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
from pyface.qt import QtGui
from traits.api import Str, Event
from traits.trait_types import Any
# ============= standard library imports ========================
import os
from PySide import QtCore
from PySide.QtCore import QRect
from PySide.QtGui import QWidget, QImageReader, QPixmap
# ============= local library imports  ==========================
from traitsui.qt4.basic_editor_factory import BasicEditorFactory
from traitsui.qt4.editor import Editor
from pychron.envisage.resources import icon


class AnimatedWidget(QWidget):
    _count = None

    def __init__(self, image):
        super(AnimatedWidget, self).__init__()
        self._images = {}

        self.image = image
        hbox = QtGui.QHBoxLayout(self)

        lbl = QtGui.QLabel(self)
        self.label = lbl
        name = image.name
        for d in image.search_path:
            if isinstance(d, str):
                p = os.path.join(d, name)
                if os.path.isfile(p):
                    self._path = p
                    break

        hbox.addWidget(lbl)
        self.setLayout(hbox)

    def set_count(self, v):
        self._set_image(v)

    def get_count(self):
        pass

    count = QtCore.Property(int, get_count, set_count)
    _column_cnt = 8

    def _set_image(self, v):
        if v != self._count:
            self._count = v
            if v in self._images:
                pix = self._images[v]
            else:
                reader = QImageReader(self._path)

                c = v % self._column_cnt
                r = v / self._column_cnt
                w, h = 22, 22
                reader.setClipRect(QRect(c * w, r * h, w, h))

                pix = QPixmap()
                pix.convertFromImage(reader.read())
                self._images[v] = pix

            self.label.setPixmap(pix)


class _AnimatedPNGEditor(Editor):
    _animation = Any
    state = Event
    _state = False

    def init(self, parent):
        self.control = self._create_control(parent)
        self.sync_value(self.factory.state, 'state', 'from')

    def _create_control(self, parent):
        widget = AnimatedWidget(icon(self.value))
        return widget

    def update_editor(self):
        pass

    def _state_fired(self):
        if not self._state:
            anim = QtCore.QPropertyAnimation(self.control, "count")

            anim.setDuration(1000)
            anim.setStartValue(1)
            anim.setEndValue(32)
            anim.setLoopCount(-1)
            QtCore.QObject.connect(anim, QtCore.SIGNAL("finished()"), anim, QtCore.SLOT("deleteLater()"))
            anim.start()

            self._animation = anim

        else:

            self._animation.stop()
            self.control.set_count(0)
        self._state = not self._state


class AnimatedPNGEditor(BasicEditorFactory):
    klass = _AnimatedPNGEditor
    state = Str

# ============= EOF =============================================




