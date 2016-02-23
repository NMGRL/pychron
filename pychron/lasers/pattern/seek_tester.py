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
import math
from threading import Thread

from chaco.default_colormaps import jet
from traits.api import HasTraits, Bool, Float, Instance, Button
from traitsui.api import View, UItem, HGroup, VGroup

# ============= standard library imports ========================
import time
from numpy import zeros, ogrid
# ============= local library imports  ==========================
from pychron.graph.graph import Graph
from pychron.lasers.pattern.dragonfly_pattern import dragonfly, DragonFlyPattern
from pychron.lasers.pattern.pattern_executor import CurrentPointOverlay
from pychron.mv.lumen_detector import LumenDetector


class LM:
    def __init__(self):
        self.stage_manager = SM()


class SM:
    pxpermm = 23

    def __init__(self):
        self.lumen_detector = LumenDetector()

    def update_axes(self):
        pass

    def moving(self, **kw):
        return False

    def find_target(self):
        return self.lumen_detector.find_target(self.frame)

    def find_best_target(self):
        return self.lumen_detector.find_best_target(self.frame)


class Controller:
    def linear_move(self, *args, **kw):
        pass


class SeekTester(HasTraits):
    cx = Float(1)
    cy = Float(1)
    width = Float(2)
    height = Float(2)
    radius = Float(0.5)
    src_graph = Instance(Graph)
    pos_graph = Instance(Graph)

    start_button = Button
    stop_button = Button
    pxpermm = Float(23)
    alive = Bool

    def _start(self):
        self.alive = True

        lm = LM()

        frm = self._frame(0, 0)
        lm.stage_manager.frame = frm

        t = Thread(target=self._dragon, args=(lm,))
        t.setDaemon(True)
        t.start()

        t = Thread(target=self._run, args=(lm,))
        t.setDaemon(True)
        t.start()

    def _stop(self):
        self.alive = False

    def _dragon(self, lm):
        pattern = DragonFlyPattern()
        controller = Controller()

        st = time.time()
        plot = self.src_graph.plots[1]
        dragonfly(st, pattern, lm, controller, plot, self._cp)

    def _run(self, lm):
        cnt = 0
        p = self.src_graph.plots[0]
        while self.alive:
            x, y = self._get_xy(cnt)
            frm = self._frame(x, y)
            p.data.set_data('imagedata', frm)
            lm.stage_manager.frame = frm
            time.sleep(0.25)
            cnt += 1

    def _get_xy(self, cnt):
        # x, y = self.cx * self.pxpermm, self.cy * self.pxpermm
        # x, y = 0, 0
        # x += cnt * 0.01
        # y += cnt * 0.01

        x = 0.3 * math.cos(math.radians((15 * cnt) % 360))
        y = 0.3 * math.sin(math.radians((15 * cnt) % 360))
        # print 'xy {},{}'.format(int(x * self.pxpermm), int(y * self.pxpermm))
        return x, y

    def _frame(self, ox, oy):
        cx, cy = self.width / 2., self.height / 2.
        cx += ox
        cy += oy

        cx, cy = self.pxpermm * cx, self.pxpermm * cy
        # cx, cy = self.cx * self.pxpermm, self.cy * self.pxpermm
        src = zeros((int(self.width * self.pxpermm), int(self.height * self.pxpermm)))
        radius = int(self.radius * self.pxpermm)
        y, x = ogrid[-radius:radius, -radius:radius]
        index = x ** 2 + y ** 2 <= radius ** 2

        src[cy - radius:cy + radius, cx - radius:cx + radius][index] = 255
        return src

    def traits_view(self):
        src = HGroup(UItem('src_graph', style='custom'))
        bgrp = HGroup(UItem('start_button'), UItem('stop_button', enabled_when='alive'))
        pgrp = VGroup(UItem('pos_graph', style='custom'))
        v = View(VGroup(bgrp, src,
                        # pgrp
                        ), resizable=True)
        return v

    def _start_button_fired(self):
        self._start()

    def _stop_button_fired(self):
        self._stop()

    def _src_graph_default(self):
        g = Graph()
        p = g.new_plot(padding_top=10)
        p.data.set_data('imagedata', zeros((self.height * self.pxpermm,
                                            self.width * self.pxpermm)))
        p.img_plot('imagedata', colormap=jet)

        p = g.new_plot(padding_bottom=10)
        p.data.set_data('imagedata', zeros((self.height * self.pxpermm,
                                            self.width * self.pxpermm)))
        p.img_plot('imagedata', colormap=jet)

        return g

    def _pos_graph_default(self):
        g = Graph()
        p = g.new_plot()
        s, p = g.new_series()
        cp = CurrentPointOverlay(component=s)
        s.overlays.append(cp)
        self._cp = cp
        return g


if __name__ == '__main__':
    s = SeekTester()
    s.configure_traits()
# ============= EOF =============================================
