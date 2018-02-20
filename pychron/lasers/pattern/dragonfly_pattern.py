# ===============================================================================
# Copyright 2016 Jake Ross
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
from __future__ import absolute_import
from traits.api import Enum, Int, Float, Str
from traitsui.api import View, Item, UItem, HGroup, VGroup
# ============= standard library imports ========================
from numpy import zeros, uint8
from chaco.default_colormaps import hot
# ============= local library imports  ==========================
from pychron.lasers.pattern.pattern_generators import line_spiral_pattern
from pychron.lasers.pattern.seek_pattern import SeekPattern
from six.moves import range


def outward_square_spiral(base):
    def gen():

        b = base
        prevx, prevy = b, 0
        while 1:
            for cnt in range(4):
                if cnt == 0:
                    x, y = b, prevy
                elif cnt == 1:
                    x, y = prevx, b
                elif cnt == 2:
                    x, y = prevx - b * 2, prevy
                elif cnt == 3:
                    x, y = prevx, prevy - b * 2
                    b *= 1.1
                prevx, prevy = x, y
                yield x, y

    return gen()


class DragonFlyPeakPattern(SeekPattern):
    spiral_kind = Enum('Hexagon', 'Square')
    min_distance = Int
    aggressiveness = Float(1)
    update_period = Int(150)
    average_saturation = Float
    position_str = Str
    move_threshold = Float(0.033)
    blur = Int

    def execution_graph_view(self):
        display_grp = HGroup(Item('average_saturation', style='readonly'),
                             Item('position_str', style='readonly'))

        v = View(VGroup(display_grp,
                        UItem('execution_graph', style='custom')),
                 x=100,
                 y=100,
                 width=500, title='Executing {}'.format(self.name))
        return v

    def setup_execution_graph(self, nplots=1):
        g = self.execution_graph

        def new_plot():
            # peak location
            imgplot = g.new_plot(padding_right=10)
            imgplot.aspect_ratio = 1.0
            imgplot.x_axis.visible = False
            imgplot.y_axis.visible = False
            imgplot.x_grid.visible = False
            imgplot.y_grid.visible = False

            imgplot.data.set_data('imagedata', zeros((5, 5, 3), dtype=uint8))
            imgplot.img_plot('imagedata', colormap=hot, origin='top left')
            return imgplot

        return [new_plot() for _ in range(nplots)]

        # img = new_plot()
        # peaks = new_plot()

        # return img, peaks

    def point_generator(self):
        if self.spiral_kind.lower() == 'square':
            return outward_square_spiral(self.base)
        else:
            return line_spiral_pattern(0, 0, self.base, 200, 0.75, 6)

    def maker_view(self):
        v = View(Item('manual_total_duration', label='Total Duration (s)',
                      tooltip='Total duration of search (in seconds)'),
                 Item('duration',
                      label='Dwell Duration (s)',
                      tooltip='Amount of time (in seconds) to wait at each point. '
                              'The brightness value is average of all measurements taken '
                              'while moving AND waiting at the vertex'),
                 Item('pre_seek_delay', label='Pre Search Delay (s)',
                      tooltip='Turn laser on and wait N seconds before starting search'),
                 Item('velocity',
                      label='Velocity (mm/s)'),
                 Item('perimeter_radius',
                      label='Perimeter Radius (mm)',
                      tooltip='Limit the search to a circular area with this radius (in mm)'),
                 Item('base',
                      label='Side (mm)',
                      tooltip="Length (in mm) of the search triangle's side"),
                 Item('min_distance', label='Minimum pixel peak radius'),
                 Item('saturation_threshold', label='Saturation Threshold',
                      tooltip='If the saturation score is greater than X then do not move'),
                 Item('aggressiveness', label='Move Aggressiveness',
                      tooltip='Tuning factor to dampen the magnitude of moves, '
                              '0<aggressiveness<1==reduce motion, >1 increase motion'),
                 Item('update_period'),
                 Item('move_threshold'),
                 Item('blur'),
                 Item('mask_kind', label='Mask', tooltip="Define the lumen detector's mask as Hole, Beam, Custom."
                                                         "Beam= Beam radius + 10%\n"
                                                         "Hole= Hole radius"),
                 Item('custom_mask_radius', label='Mask Radius (mm)',
                      visible_when='mask_kind=="Custom"'))
        return v

# ============= EOF =============================================
