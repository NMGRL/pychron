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
from traits.api import Int, Instance
# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.basic_editor_factory import BasicEditorFactory
from traitsui.qt4.editor import Editor


class _CameraEditor(Editor):
    timer = Instance(QTimer)
    swap = False

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
        img = self.value.get_image_data()
        if img is not None:
            s = img.shape
            if s:
                im = QImage(img, s[1], s[0], QImage.Format_RGB32)
                # im = QImage(img, s[1], s[0], QImage.Format_RGB16)
                if self.swap:
                    im = QImage.rgbSwapped(im)

                pix = QPixmap.fromImage(im)
                self.control.setPixmap(pix)

    def _create_control(self, parent):
        label = QLabel()
        width, height = self.item.width, self.item.height
        if self.item.width != -1.0:
            label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            label.setFixedWidth(abs(width))
            label.setFixedHeight(abs(height))
        return label


class  CameraEditor(BasicEditorFactory):
    klass = _CameraEditor
    fps = Int(24)

# ============= EOF =============================================



