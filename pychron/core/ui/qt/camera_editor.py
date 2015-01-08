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
from PySide.QtCore import QTimer
from PySide.QtGui import QLabel, QImage, QPixmap, QSizePolicy
from pyface.qt import QtCore
from traits.api import HasTraits, Button, Int, Instance
from traitsui.api import View, Item
# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.qt4.basic_editor_factory import BasicEditorFactory
from traitsui.qt4.editor import Editor


class _CameraEditor(Editor):
    timer = Instance(QTimer)

    def init(self, parent):
        self.control = self._create_control(parent)

    def update_editor(self):
        self._setup_loop()

    def dispose(self):
        self.timer.stop()

    def _setup_loop(self):
        self.timer = QTimer(self.control)
        self.timer.timeout.connect(self._update)
        if self.factory.fps:
            self.timer.setInterval(1000 / self.factory.fps)
        self.timer.start()

    def _update(self):
        # w, h = self.control.width(), self.control.height()
        # img = self.value.get_image_data(size=(w, h))
        img = self.value.get_image_data(size=(640,480))
        s = img.shape
        if s:
            im = QImage(img, s[1], s[0], QImage.Format_RGB888)
            pix = QPixmap.fromImage(QImage.rgbSwapped(im))
            self.control.setPixmap(pix)

    def _create_control(self, parent):
        label = QLabel()
        # label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        # sp = label.sizePolicy()
        # sp.setHeightForWidth(True)
        # label.setFixedWidth(640)
        # label.setFixedHeight(480)
        parent.addWidget(label)
        return label


class CameraEditor(BasicEditorFactory):
    klass = _CameraEditor
    fps = Int(24)

# ============= EOF =============================================



