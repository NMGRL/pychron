# ===============================================================================
# Copyright 2011 Jake Ross
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
import os

import vlc
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from pyface.qt import QtGui
from pyface.qt.QtGui import QWidget, QImage, QPixmap, QSlider, QVBoxLayout, QPushButton, QStyle, QFrame, QLabel
from traits.has_traits import HasTraits
from traits.trait_types import Str
from traitsui.basic_editor_factory import BasicEditorFactory
from traitsui.item import UItem
from traitsui.qt.editor import Editor
from traitsui.view import View


# from pychron.image.cv_wrapper import get_capture_device


class VideoWidget(QWidget):
    path = Str

    def __init__(self, *args, **kw):
        super(VideoWidget, self).__init__(*args, **kw)

        self.playButton = QPushButton()
        self.playButton.setEnabled(True)
        self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.playButton.clicked.connect(self.play)

        self.positionSlider = QSlider(Qt.Horizontal)
        self.positionSlider.setRange(0, 100)

        layout = QtGui.QVBoxLayout()

        controlLayout = QtGui.QHBoxLayout()
        controlLayout.setContentsMargins(0, 0, 0, 0)
        controlLayout.addWidget(self.playButton)
        controlLayout.addWidget(self.positionSlider)
        self.path = '/Users/ross/Desktop/67900-83-0011.m4v'
        #     # hbox = QtGui.QHBoxLayout(self)
        #     # vbox = QtGui.QVBoxLayout(self)
        #     # vbox.addLayout(controlLayout)
        # lbl = QtGui.QLabel()
        from PyQt5.QtWidgets import QMacCocoaViewContainer
        # self.videoframe = QMacCocoaViewContainer(0)
        self.videoframe = QFrame(self)
        self.playlist = ['/Users/ross/Desktop/67900-83-001.avi']
        # Define the VLC-specific variables we're going to use
        self.vlc_instance = vlc.Instance('--quiet')
        self.vlc_player = self.vlc_instance.media_list_player_new()
        self.media_list = self.vlc_instance.media_list_new(self.playlist)

        # Create the user interface, set up the player, and play the 2 videos
        # self.create_user_interface()
        self.video_player_setup()
        #     self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        #
        #     videoWidget = QVideoWidget()
        #
        # self.resize(100, 100)
        # self.videoframe.resize(100, 100)
        self.videoframe.setGeometry(10, 50, 640, 480)
        self.setGeometry(10, 50, 640, 480)
        self.vlc_player.play()

        # layout.addWidget(self.videoframe)
        # layout.addLayout(controlLayout)
        # self.setLayout(layout)

        #     layout.addWidget(videoWidget)
        #     # self.cap = get_capture_device()
        #     # self.cap.open(0)
        #     lbl.setPixmap(image.create_image())
        #     self.set_frame()
        #     # hbox.addWidget(videoWidget)
        #     # vbox.addWidget(videoWidget)
        #     # layout.addLayout()
        #     # print('asdf', hbox)
        #     # self.setLayout(vbox)
        #
        #     self.mediaPlayer.setVideoOutput(videoWidget)
        #     self.mediaPlayer.error.connect(self.handleError)
        #
        #     print('osdf', os.path.isfile(self.path), self.path)
        #     self.mediaPlayer.setMedia(
        #         QMediaContent(QUrl.fromLocalFile(self.path)))
        #     # self.mediaPlayer.play()
        #     self.startTimer(100)
        # self.setLayout(layout)

    #
    # def handleError(self):

    #     print(self.mediaPlayer.errorString())

    def video_player_setup(self):
        """Sets media list for the VLC player and then sets VLC's output to the video frame"""
        self.vlc_player.set_media_list(self.media_list)
        self.vlc_player.get_media_player().set_nsobject(int(self.videoframe.winId()))

    def create_user_interface(self):
        """Create a 1280x720 UI consisting of a vertical layout, central widget, and QLabel"""
        # self.setCentralWidget(self.central_widget)
        # self.vertical_box_layout.addWidget(self.video_frame)
        # self.central_widget.setLayout(self.vertical_box_layout)

        # self.resize(1280, 720)

    def play(self):
        print('afafafafafa')
        self.vlc_player.play()

    #     if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
    #         self.mediaPlayer.pause()
    #     else:
    #         print('plinasf')
    #         self.mediaPlayer.play()

    # def timerEvent(self, *args, **kwargs):
    #     self.set_frame()
    #
    # def set_frame(self):
    #     pass
    #     # ok, data = self.cap.read()
    #     # shape = data.shape
    #     # im = QImage(data, shape[1], shape[0], QImage.Format_RGB888)
    #     # pix = QPixmap.fromImage(QImage.rgbSwapped(im))
    #     # self.label.setPixmap(pix)


class _VideoEditor(Editor):
    def init(self, parent):
        self.control = self._create_control()

    def _create_control(self):
        videoframe = QLabel()
        # videoframe.setGeometry(0, 0, 640, 480)
        playlist = ['/Users/ross/Desktop/67900-83-001.avi']
        # Define the VLC-specific variables we're going to use
        vlc_instance = vlc.Instance()
        vlc_player = vlc_instance.media_list_player_new()
        media_list = vlc_instance.media_list_new(playlist)
        vlc_player.set_media_list(media_list)
        vlc_player.get_media_player().set_nsobject(int(videoframe.winId()))
        vlc_player.play()

        return videoframe

    def update_editor(self):
        pass


class VideoEditor(BasicEditorFactory):
    klass = _VideoEditor


class Demo(HasTraits):
    a = Str('aa')

    # state = Button

    def traits_view(self):
        v = View(UItem('a', editor=VideoEditor(),
                       width=640,
                       height=480),
                 # UItem('state'),
                 # width=700,
                 # height=520,
                 resizable=True
                 )
        return v


d = Demo()
d.configure_traits()
# # ============= enthought library imports =======================
# from traits.api import DelegatesTo, Instance
# from traitsui.api import View, Item, HGroup, spring
#
# # ============= standard library imports ========================
# import sys
# import os
# # ============= local library imports  ==========================
# # add pychron to the path
# root = os.path.basename(os.path.dirname(__file__))
# if 'pychron_beta' not in root:
# root = 'pychron_beta'
# src = os.path.join(os.path.expanduser('~'),
#                    'Programming',
#                    root
# )
# sys.path.append(src)
#
# from pychron.lasers.stage_managers.video_component_editor import VideoComponentEditor
# from pychron.managers.videoable import Videoable
# from pychron.canvas.canvas2D.video_laser_tray_canvas import VideoLaserTrayCanvas
#
#
# class VideoDisplayCanvas(VideoLaserTrayCanvas):
#     show_grids = False
#     show_axes = False
#     use_camera = False
#
#
# class VideoPlayer(Videoable):
#     canvas = Instance(VideoDisplayCanvas)
#     crosshairs_kind = DelegatesTo('canvas')
#     crosshairs_color = DelegatesTo('canvas')
#
#     def _canvas_default(self):
#         self.video.open(user='underlay')
#         return VideoDisplayCanvas(padding=30,
#                                   video=self.video_manager.video)
#
#     def traits_view(self):
#         vc = Item('canvas',
#                   style='custom',
#                   editor=VideoComponentEditor(width=640, height=480),
#                   show_label=False,
#                   resizable=False,
#
#         )
#         v = View(
#
#             HGroup(spring, Item('crosshairs_kind'), Item('crosshairs_color')),
#             vc,
#             #                 width = 800,
#             height=530,
#             title='Video Display'
#         )
#         return v
#
#
# if __name__ == '__main__':
#     v = VideoPlayer()
#     v.configure_traits()
# ============= EOF ====================================
