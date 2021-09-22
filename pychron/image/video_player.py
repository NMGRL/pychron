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

from traits.api import HasTraits, Str
from traitsui.api import View, UItem
from pychron.core.ui.video_editor import VideoEditor


class VideoPlayer(HasTraits):
    video_path = Str
    title = Str

    def traits_view(self):
        v = View(UItem('video_path', editor=VideoEditor(), width=640, height=480),
                 title = self.title,
                 resizable=True)
        return v


if __name__ == '__main__':
    vp = VideoPlayer()
    vp.video_path = '/Users/ross/Desktop/67900-83-001.avi'
    vp.configure_traits()

# ============= EOF =============================================
