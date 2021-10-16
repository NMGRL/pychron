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

import vlc
from PyQt5.QtWidgets import QLabel
from traitsui.qt4.basic_editor_factory import BasicEditorFactory
from traitsui.qt4.editor import Editor

from traits.api import Any


class _VideoEditor(Editor):
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


class VideoEditor(BasicEditorFactory):
    klass = _VideoEditor


# ============= EOF =============================================
