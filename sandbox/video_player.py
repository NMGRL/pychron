# ===============================================================================
# Copyright 2011 Jake Ross
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
from traits.api import DelegatesTo, Instance
from traitsui.api import View, Item, HGroup, spring

#============= standard library imports ========================
import sys
import os
#============= local library imports  ==========================
# add pychron to the path
root = os.path.basename(os.path.dirname(__file__))
if 'pychron_beta' not in root:
    root = 'pychron_beta'
src = os.path.join(os.path.expanduser('~'),
                   'Programming',
                   root
)
sys.path.append(src)

from pychron.lasers.stage_managers.video_component_editor import VideoComponentEditor
from pychron.managers.videoable import Videoable
from pychron.canvas.canvas2D.video_laser_tray_canvas import VideoLaserTrayCanvas


class VideoDisplayCanvas(VideoLaserTrayCanvas):
    show_grids = False
    show_axes = False
    use_camera = False


class VideoPlayer(Videoable):
    canvas = Instance(VideoDisplayCanvas)
    crosshairs_kind = DelegatesTo('canvas')
    crosshairs_color = DelegatesTo('canvas')

    def _canvas_default(self):
        self.video.open(user='underlay')
        return VideoDisplayCanvas(padding=30,
                                  video=self.video_manager.video)

    def traits_view(self):
        vc = Item('canvas',
                  style='custom',
                  editor=VideoComponentEditor(width=640, height=480),
                  show_label=False,
                  resizable=False,

        )
        v = View(

            HGroup(spring, Item('crosshairs_kind'), Item('crosshairs_color')),
            vc,
            #                 width = 800,
            height=530,
            title='Video Display'
        )
        return v


if __name__ == '__main__':
    v = VideoPlayer()
    v.configure_traits()
#============= EOF ====================================
