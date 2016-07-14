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

# =============enthought library imports=======================
from pyface.timer.do_later import do_after
from traits.api import Any
# from traitsui.api import View, Item, VGroup, HGroup, ColorEditor
# =============standard library imports ========================
# import math
# =============local library imports  ==========================
from pychron.canvas.canvas2D.crosshairs_overlay import SimpleCrosshairsOverlay
from pychron.canvas.canvas2D.stage_canvas import StageCanvas

DIRECTIONS = {'Left': ('x', -1), 'Right': ('x', 1),
              'Down': ('y', -1), 'Up': ('y', 1)}


class FurnaceCanvas(StageCanvas):
    """
    """
    render_map = True
    bgcolor = 'mediumturquoise'

    feeder = Any

    aspect_ratio = 3.

    def __init__(self, *args, **kw):
        super(FurnaceCanvas, self).__init__(*args, **kw)
        self.border_visible = False
        self.show_axes = True
        self.use_zoom = False
        self.use_pan = False

        self._add_crosshairs(klass=SimpleCrosshairsOverlay)
        self.crosshairs_overlay.radius = 0.5
        self.crosshairs_overlay.constrain = 'y'
        # self.show_laser_position = False
        # self.show_current_position = False

        self.view_y_range = (-5, 5)
        self.view_x_range = (0, 140)
        self.padding_top = 5
        self.padding_bottom = 5
        self.use_valid_holes = False
        self.show_indicators = False

    def set_map(self, mp):
        super(FurnaceCanvas, self).set_map(mp)

        xs = [h.x for h in mp.sample_holes]
        xmi, xma = min(xs), max(xs)
        pad = mp.g_dimension
        self.view_x_range = (xmi - pad, xma + pad)

    def clear_all(self):
        self.scene.reset_layers()

    def valid_position(self, x, y):
        """
        """
        between = lambda mi, v, ma: mi < v <= ma
        return between(self.x, x, self.x2) and between(self.y, y, self.y2)

    #         if self.stage_manager is not None:
    #             p = self.stage_manager.stage_controller
    #
    #             x, y = self.map_data((x, y))
    #             try:
    #                 if between(p.xaxes_min, x, p.xaxes_max) and \
    #                         between(p.yaxes_min, y, p.yaxes_max):
    #                     return x, y
    #             except AttributeError, e:
    #                 print e
    # ===============================================================================
    # interactor
    # ===============================================================================
    def normal_left_down(self, event):
        """
        """
        x = event.x
        y = event.y

        if self.valid_position(x, y):
            x, y = self.map_data((x, y))
            self.set_desired_position(x, y)

            self.feeder.set_position(x, units='mm')
            do_after(50, self._update_position)
            event.handled = True

    def normal_key_pressed(self, event):
        c = event.character
        if c in ('Left', 'Right'):
            ax_key, direction = DIRECTIONS[c]
            distance = 5 if event.shift_down else 1
            self.feeder.slew(direction * distance)
            event.handled = True
            self.event_state = 'slew'

    def key_released(self, char):
        """
            called from outside by StageCompnentEditor
        """
        self.feeder.stop()
        self._update_stage_position()
        self.event_state = 'normal'

    # ===============================================================================
    # private
    # ===============================================================================
    def _update_stage_position(self):
        pos = self.feeder.get_position(units='mm')
        self.set_stage_position(pos, 0)

    def _update_position(self):
        self._update_stage_position()
        if self.feeder.moving():
            do_after(250, self._update_position)

            # ===============================================================================
            # handlers
            # ===============================================================================

            # ===============================================================================
            # defaults
            # ===============================================================================

# ========================EOF====================================================
