# ===============================================================================
# Copyright 2021 ross
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
from PyQt5 import QtWidgets
from PyQt5.QtCore import QTimer, QSize, Qt, QPoint
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen
from pyface.qt import QtCore
from traitsui.basic_editor_factory import BasicEditorFactory

try:
    import vlc
except ImportError:
    pass
from PyQt5.QtWidgets import QLabel
from traitsui.qt4.editor import Editor

from traits.api import Any


class _VLCVideoEditor(Editor):
    vlc_instance = Any
    vlc_player = Any

    def init(self, parent):
        self.control = self._create_control()

    def _create_control(self):
        videoframe = QLabel()
        # videoframe.setGeometry(0, 0, 640, 480)
        playlist = [self.value]
        # Define the VLC-specific variables we're going to use
        self.vlc_instance = vlc.Instance()
        self.vlc_player = self.vlc_instance.media_list_player_new()
        media_list = self.vlc_instance.media_list_new(playlist)
        self.vlc_player.set_media_list(media_list)
        self.vlc_player.get_media_player().set_nsobject(int(videoframe.winId()))
        self.vlc_player.play()

        return videoframe

    def update_editor(self):
        if self.value:
            media_list = self.vlc_instance.media_list_new([self.value])
            self.vlc_player.set_media_list(media_list)


class VideoFrame(QLabel):
    # def resizeEvent(self, event):
    #     super(VideoFrame, self).resizeEvent(event)
    #     print('resasd', event.size().width())
    # self.resize(event.size())

    def sizeHint(self):
        return QSize(320, 240)


class _VideoEditor(Editor):
    videoframe = Any

    def init(self, parent):
        self.control = self._create_control()
        # print(parent, parent.size())
        # parent.addWidget(self.control)

    def _create_control(self):
        frame = VideoFrame()
        frame.setScaledContents(True)
        frame.setSizePolicy(
            QtWidgets.QSizePolicy.MinimumExpanding,
            QtWidgets.QSizePolicy.MinimumExpanding,
        )
        width = self.item.width
        if width < 0:
            width = self.factory.size[0]

        height = self.item.height
        if height < 0:
            height = self.factory.size[1]

        frame.resize(width, height)
        video = self.value
        if video.cap:
            video.cap.hooks = [self._update]

        return frame

    def _update(self, img):
        if self.control:
            qp = QPainter(img)
            qp.setRenderHint(QPainter.Antialiasing)
            qp.setPen(QPen(Qt.red, 2, Qt.SolidLine))

            s = self.control.size()

            qp.drawEllipse(QPoint(img.width() / 2, img.height() / 2), 32, 32)

            pixmap = QPixmap.fromImage(img)
            pixmap4 = pixmap.scaled(s.width(), s.height(), QtCore.Qt.KeepAspectRatio)

            self.control.setPixmap(pixmap4)


class VideoEditor(BasicEditorFactory):
    klass = _VideoEditor


# ============= EOF =============================================
