# ===============================================================================
# Copyright 2015 Jake Ross
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
from chaco.abstract_overlay import AbstractOverlay
from enable.tools.drag_tool import DragTool
from kiva.trait_defs.kiva_font_trait import KivaFont
from traits.api import Event as TEvent
from traits.api import Float, List, Button, Enum

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.graph.tools.limits_tool import LimitsTool, LimitOverlay
from pychron.spectrometer.jobs.base_scanner import BaseScanner
from six.moves import zip


class ScannerBoundsTool(DragTool):
    low = Float(2)
    high = Float(6)
    _low_drag = False
    _high_drag = False
    updated = TEvent

    def set_limits(self, mi, ma):
        offset = (ma - mi) * 0.1
        mi += offset
        ma -= offset
        self.low = mi
        self.high = ma
        self.overlay.low = mi
        self.overlay.high = ma
        self.component.request_redraw()
        self.updated = (mi, ma)

    def set_low(self, v):
        offset = (self.high - v) * 0.1
        v += offset
        self.low = v
        self.overlay.low = v
        self.component.request_redraw()

    def set_high(self, v):
        offset = (v - self.low) * 0.1
        v -= offset

        self.high = v
        self.overlay.high = v
        self.component.request_redraw()

    def is_draggable(self, x, y):
        (x1, _), (x2, _) = self.component.map_screen([(self.low, 0), (self.high, 0)])
        self._low_drag = False
        self._high_drag = False
        if abs(x - x1) < 5:
            self._low_drag = True
        elif abs(x - x2) < 5:
            self._high_drag = True

        return self._low_drag or self._high_drag

    def drag_end(self, event):
        if self._low_drag:
            self.low = self.component.map_data((event.x, 0))[0]
        elif self._high_drag:
            self.high = self.component.map_data((event.x, 0))[0]
        self.updated = (self.low, self.high)

    def dragging(self, event):
        v = self.component.map_data((event.x, 0))[0]
        if self._low_drag:
            self.overlay.low = v
        elif self._high_drag:
            self.overlay.high = v
        self.component.request_redraw()
        self.updated = (self.overlay.low, self.overlay.high)


class ScannerBoundsOverlay(AbstractOverlay):
    low = Float(2)
    high = Float(6)

    def overlay(self, component, gc, view_bounds=None, mode="normal"):
        with gc:
            gc.clip_to_rect(component.x, component.y, component.width, component.height)
            y, y2 = component.y, component.y2

            (x1, _), (x2, _) = component.map_screen([(self.low, 0), (self.high, 0)])

            gc.set_stroke_color((0, 0.5, 0))
            gc.set_line_width(2.5)
            gc.move_to(x1, y)
            gc.line_to(x1, y2)

            gc.move_to(x2, y)
            gc.line_to(x2, y2)

            gc.draw_path()


class MFTableOverlay(AbstractOverlay):
    dacs = List
    one_amu_dac = Float
    isotopes = List
    font = KivaFont("Helvetica 10")

    def overlay(self, component, gc, view_bounds=None, mode="normal"):
        with gc:
            gc.clip_to_rect(component.x, component.y, component.width, component.height)
            y, y2 = component.y, component.y2

            color = (0.615, 0.823, 0.929, 0.631)
            gc.set_stroke_color(color)
            gc.set_fill_color(color)
            a, b = component.map_screen([(0, 0), (self.one_amu_dac, 0)])
            w = b[0] - a[0]
            h = y2 - y

            screen_dacs = []
            for d in self.dacs:
                x = component.map_screen([(d, 0)])[0][0]
                screen_dacs.append(x)
                gc.rect(x - w / 2.0, y, w, h)
            gc.draw_path()

            gc.set_line_width(2.5)
            gc.set_stroke_color((0, 0, 0))
            for x in screen_dacs:
                gc.move_to(x, y)
                gc.line_to(x, y2)
            gc.draw_path()

        with gc:
            gc.set_font(self.font)
            for x, iso in zip(screen_dacs, self.isotopes):
                gc.set_text_position(x, y2 + 5)
                gc.show_text(iso)


class DACScanner(BaseScanner):
    min_dac = Float(0)
    max_dac = Float(10)

    scan_min_dac = Float(1)
    scan_max_dac = Float(9)

    use_mftable_limits = Button
    scan_time_length = Enum("10 s", "20 s", "30 s", "60 s")

    help_str = "Drag the green rulers to define the scan limits"

    pattributes = ("step", "scan_min_dac", "scan_max_dac", "min_dac", "max_dac")
    tool = None

    def __init__(self, *args, **kw):
        super(DACScanner, self).__init__(*args, **kw)
        # graph = Graph()
        # self.graph = graph
        #
        # p = graph.new_plot(padding_top=30, padding_right=10)
        #
        # self._add_bounds(p)
        # self._add_mftable_overlay(p)
        # self._add_limit_tool(p)
        # p.index_range.on_trait_change(self._handle_xbounds_change, 'updated')
        # # graph.set_x_limits(self.min_dac, self.max_dac)
        # graph.new_series()
        # graph.set_x_title('Magnet DAC (Voltage)')
        # graph.set_y_title('Intensity')

        self._use_mftable_limits_fired()

    # private
    def _reset_hook(self):
        self._use_mftable_limits_fired()

    def _setup_graph(self, graph, plot):
        self._add_bounds(plot)
        self._add_mftable_overlay(plot)
        self._add_limit_tool(plot)
        plot.index_range.on_trait_change(self._handle_xbounds_change, "updated")
        graph.new_series()
        graph.set_x_title("Magnet DAC (Voltage)")
        graph.set_y_title("Intensity")

    # scan methods
    def _do_step(self, magnet, step):
        magnet.set_dac(step, verbose=False)

    def _get_limits(self):
        return self.tool.low, self.tool.high

    def _calculate_steps(self, l, h):
        self.debug("scan limits: low={}, high={}".format(l, h))
        si = l
        while 1:
            yield si
            si += self.step
            if si > h:
                yield h
                raise StopIteration
                # return gen

    # overlays
    def _add_limit_tool(self, plot):
        """
        add tool for dragging the limits of the graph

        :param plot: Plot
        """
        t = LimitsTool(component=plot, orientation="x")

        o = LimitOverlay(component=plot, tool=t)

        plot.tools.append(t)
        plot.overlays.append(o)

    def _add_mftable_overlay(self, plot):
        mft = self.spectrometer.magnet.field_table.get_table()
        try:
            isos, mws, dacs, coeffs = mft[self.spectrometer.reference_detector]
        except KeyError:
            return

        d = (dacs[1] - dacs[0]) / (mws[1] - mws[0])

        o = MFTableOverlay(dacs=list(dacs), isotopes=list(isos), one_amu_dac=d * 0.8)
        plot.underlays.append(o)

    def _add_bounds(self, plot):
        o = ScannerBoundsOverlay()
        tool = ScannerBoundsTool(component=plot, overlay=o)
        self.tool = tool
        self.tool.on_trait_change(self._handle_tool_change, "updated")
        plot.tools.append(tool)
        plot.overlays.append(o)

    # handlers
    # def _start_scanner_fired(self):
    #     print 'start scanner'
    #     self.info('starting scanner')
    #     self.new_scanner_enabled = False
    #     self.stop_scanner_enabled = True
    #     self.scan()
    #
    # def _stop_scanner_fired(self):
    #     self.stop_scan()
    #     self.stop_scanner_enabled = False
    #     self.new_scanner_enabled = True
    #
    # def _new_scanner_fired(self):
    #     print 'new scanner'
    #     self.info('new scanner')
    #     self.new_scanner_enabled = False
    #     self.start_scanner_enabled = True
    #
    # def _clear_graph_button_fired(self):
    #     self.graph.clear_plots()
    #     self.plotid = 0
    #     self.graph.redraw()

    def _use_mftable_limits_fired(self):
        mft = self.spectrometer.magnet.field_table.get_table()
        try:
            isos, mws, dacs, coeffs = mft[self.spectrometer.reference_detector]
        except KeyError:
            self.warning(
                "{} not in mftable".format(self.spectrometer.reference_detector)
            )
            return

        mi = min(dacs)
        ma = max(dacs)

        self.graph.set_x_limits(mi, ma, pad="0.1")
        self.scan_min_dac = self.tool.low
        self.scan_max_dac = self.tool.high

    def _scan_time_length_changed(self):
        mi, ma = self.scan_min_dac, self.scan_max_dac
        st = self.spectrometer.integration_time
        t = int(self.scan_time_length[:-2]) - 1  # * st
        # print t, int(self.scan_time_length[:-2]), st
        d = ma - mi
        self.step = st * d / t

    def _handle_tool_change(self, new):
        self.scan_min_dac = new[0]  # self.tool.low
        self.scan_max_dac = new[1]  # self.tool.high

    def _handle_xbounds_change(self, new):
        self.tool.set_limits(*new)
        self.min_dac = new[0]
        self.max_dac = new[1]
        self.use_scan_length = True
        if self.use_scan_length:
            self._scan_time_length_changed()

    def _scan_min_dac_changed(self):
        if self.tool:
            self.tool.low = self.scan_min_dac
            self.tool.overlay.low = self.scan_min_dac
        self._scan_time_length_changed()
        # self.graph.redraw()

    def _scan_max_dac_changed(self):
        if self.tool:
            self.tool.high = self.scan_max_dac
            self.tool.overlay.high = self.scan_max_dac
        self._scan_time_length_changed()
        # self.graph.redraw()

    def _min_dac_changed(self):
        if self.min_dac < self.max_dac:
            self.graph.set_x_limits(min_=self.min_dac)

            # self.tool.set_low(self.min_dac)

    def _max_dac_changed(self):
        if self.max_dac > self.min_dac:
            self.graph.set_x_limits(max_=self.max_dac)
            # self.tool.set_high(self.max_dac)


# ============= EOF =============================================
