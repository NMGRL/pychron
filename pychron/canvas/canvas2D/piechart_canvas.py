#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.canvas.canvas2D.scene.pie_chart_scene import PieChartScene
from pychron.canvas.canvas2D.scene.scene_canvas import SceneCanvas


class PieChartCanvas(SceneCanvas):
    use_pan = False
    use_zoom = False
    #     fill_padding = True
    #     bgcolor = 'red'
    border_visible = False
    show_axes = False
    show_grids = False

    # padding_top = 0
    # padding_bottom = 0
    # padding_left = 0
    # padding_right = 0

    # aspect_ratio = 1

    def load_scene(self, p):
        s=PieChartScene()
        s.load(p)

        self.scene=s

        self.index_axis.tick_visible = False
        self.value_range.tight_bounds=False

        # self.value_range.low = 0
        # self.value_range.high = 100
        #
        # self.index_range.low = -2
        # self.index_range.high = 10
        #
        # self.value_axis.title = 'Elevation (m. asl)'
        # self.index_axis.title = 'Age (Ma)'
        # s = StratScene()
        # s.load(p)
        # self.scene = s
        #
        # low, high = s.value_limits
        # pad = (high - low) * 0.1
        # self.value_range.low_setting = low - pad
        # self.value_range.high_setting = high + pad
        #
        # low, high = s.index_limits
        # pad = (high - low) * 0.1
        # self.index_range.low_setting = io = low - pad
        # self.index_range.high_setting = high + pad
        #
        # for i in self.scene.iteritems():
        #     i.index_origin = io

#============= EOF =============================================

