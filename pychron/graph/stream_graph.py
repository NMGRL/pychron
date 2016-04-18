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

from pychron.core.ui import set_qt

set_qt()
# =============enthought library imports=======================
from pyface.timer.api import do_after as do_after_timer
# =============standard library imports ========================
from numpy import hstack, Inf
import time
# =============local library imports  ==========================
# from pychron.graph.editors.stream_plot_editor import StreamPlotEditor
from stacked_graph import StackedGraph
from graph import Graph

MAX_LIMIT = int(-1 * 60 * 60 * 24)


def time_generator(start):
    """
    """
    yt = start
    prev_time = 0
    while 1:

        current_time = time.time()
        if prev_time != 0:
            interval = current_time - prev_time
            yt += interval

        yield yt
        prev_time = current_time


class StreamGraph(Graph):
    """
    """
    # plot_editor_klass = StreamPlotEditor
    global_time_generator = None

    cur_min = None
    cur_max = None

    # track_y_max = Bool(True)
    #    track_y_min = Bool(True)
    #
    #    track_x_max = Bool(True)
    #    track_x_min = Bool(True)
    #
    #
    #    force_track_x_flag = False

    track_y_max = None
    track_y_min = None

    track_x_max = None
    track_x_min = None

    force_track_x_flag = None

    def __init__(self, *args, **kw):
        super(StreamGraph, self).__init__(*args, **kw)
        self.scan_delays = []
        self.time_generators = []
        self.data_limits = []
        self.scan_widths = []

    def clear(self):
        self.scan_delays = []
        self.time_generators = []
        self.data_limits = []
        self.scan_widths = []

        self.cur_min = []
        self.cur_max = []
        self.track_x_max = True
        self.track_x_min = True
        self.track_y_max = []
        self.track_y_min = []
        self.force_track_x_flag = False

        super(StreamGraph, self).clear()

    def new_plot(self, **kw):
        """
        """
        dl = kw.get('data_limit', 500)
        sw = kw.get('scan_width', 60)

        self.scan_widths.append(sw)
        self.data_limits.append(dl)
        self.cur_min.append(Inf)
        self.cur_max.append(-Inf)

        self.track_y_max.append(True)
        self.track_y_min.append(True)

        args = super(StreamGraph, self).new_plot(**kw)

        self.set_x_limits(min_=0, max_=sw * 1.05, plotid=len(self.plots) - 1)

        return args

    def update_y_limits(self, plotid=0, **kw):
        ma = -1
        mi = 1e10
        for _k, v in self.plots[plotid].plots.iteritems():
            ds = v[0].value.get_data()
            try:
                ma = max(ma, max(ds))
                mi = min(mi, min(ds))
            except ValueError:
                return

        if not self.track_y_max[plotid]:
            ma = None

        if not self.track_y_min[plotid]:
            mi = None

        self.set_y_limits(min_=mi, max_=ma, plotid=plotid, pad=5, **kw)

    def set_scan_width(self, v, plotid=0):
        self.scan_widths[plotid] = v

    def set_data_limits(self, d, plotid=None):
        if plotid is None:
            for i in xrange(len(self.plots)):
                self.data_limits[i] = d
        else:
            self.data_limits[plotid] = d

    def set_scan_widths(self, d, plotid=None):
        if plotid is None:
            for i in xrange(len(self.plots)):
                self.scan_widths[i] = d
        else:
            self.scan_widths[plotid] = d

    def _set_xlimits(self, ma, plotid):
        sw = self.scan_widths[plotid]
        if ma < sw:
            mi = 0
            ma = sw * 1.05
        else:
            mi = ma - sw
            ma += sw * 0.05

        self.set_x_limits(max_=ma,
                          min_=mi,
                          plotid=plotid)

    def record(self, y, x=None, series=0, plotid=0, track_x=True, track_y=True):
        xn, yn = self.series[plotid][series]

        plot = self.plots[plotid]

        xd = plot.data.get_data(xn)
        yd = plot.data.get_data(yn)
        if x is None:
            try:
                tg = self.time_generators[plotid]
            except IndexError:
                tg = time_generator(0)
                self.time_generators.append(tg)
            nx = tg.next()
        else:
            nx = x

        dl = self.data_limits[plotid]

        if self.force_track_x_flag or (track_x and (self.track_x_min or self.track_x_max)):
            self._set_xlimits(nx, plotid)

        if track_y and (self.track_y_min[plotid] or self.track_y_max[plotid]):

            if not self.track_y_max[plotid]:
                ma = None
            else:
                ma = self.cur_max[plotid]

            if not self.track_y_min[plotid]:
                mi = None
            else:
                mi = self.cur_min[plotid]

            self.set_y_limits(max_=ma,
                              min_=mi,
                              pad='0.1',
                              plotid=plotid)
        lim = int(-dl)

        new_xd = hstack((xd[lim:], [nx]))
        new_yd = hstack((yd[lim:], [float(y)]))

        plot.data.set_data(xn, new_xd)
        plot.data.set_data(yn, new_yd)

        self.cur_max[plotid] = max(self.cur_max[plotid], max(new_yd))
        self.cur_min[plotid] = min(self.cur_min[plotid], min(new_yd))
        return nx

    def record_multiple(self, ys, plotid=0, track_y=True):
        tg = self.global_time_generator
        if tg is None:
            tg = time_generator(0)
            self.global_time_generator = tg

        x = tg.next()
        for i, yi in enumerate(ys):
            self.record(yi, x=x, series=i, track_x=False, track_y=track_y)

        ma = max(ys)
        mi = min(ys)
        if ma < self.cur_max[plotid]:
            self.cur_max[plotid] = -Inf
        if mi > self.cur_min[plotid]:
            self.cur_min[plotid] = Inf

        self._set_xlimits(x, plotid=plotid)
        return x


class StreamStackedGraph(StreamGraph, StackedGraph):
    pass


if __name__ == '__main__':
    from traits.has_traits import HasTraits
    from traits.trait_types import Button
    import random
    from traitsui.view import View


    class Demo(HasTraits):
        test = Button

        def _test_fired(self):
            s = StreamGraph()
            s.new_plot(scan_width=5)
            s.new_series(type='scatter')
            s.new_series(type='line', plotid=0)
            s.new_series(type='line', plotid=0)

            s.edit_traits()
            self.g = s
            do_after_timer(1000, self._iter)

        def _iter(self):
            st = time.time()
            ys = [random.random(), random.random(), random.random()]
            self.g.record_multiple(ys)
            # self.g.record(random.random())

            do_after_timer(999.5 - (time.time() - st) * 1000, self._iter)

        def traits_view(self):
            v = View('test')
            return v


    d = Demo()

    d.configure_traits()
# ============= EOF ====================================
# def record_multiple(self, ys, plotid=0, scalar=1, track_x=True, **kw):
#
#     tg = self.global_time_generator
#     if tg is None:
#         tg = time_generator(self.scan_delays[plotid])
#         self.global_time_generator = tg
#
#     x = tg.next() * scalar
#     for i, yi in enumerate(ys):
#         kw['track_x'] = False
#         self.record(yi, x=x, series=i, **kw)
#
#     ma = max(ys)
#     mi = min(ys)
#     if ma < self.cur_max[plotid]:
#         self.cur_max[plotid] = -Inf
#     if mi > self.cur_min[plotid]:
#         self.cur_min[plotid] = Inf
#
#     if track_x:
#         # dl = self.data_limits[plotid]
#         # mi = max(1, x - dl * self.scan_delays[plotid])
#         # ma = max(x*1.05, mi+)
#         sw = self.scan_widths[plotid]
#         if sw:
#             ma = max(x*1.05, sw)
#             mi = 0
#             if ma > sw:
#                 mi = ma-sw
#         else:
#             ma = None
#             dl = self.data_limits[plotid]
#             mi = max(1, x - dl * self.scan_delays[plotid])
#
#         self.set_x_limits(max_=ma,
#                           min_=mi,
#                           plotid=plotid)
#     return x
#
# def record(self, y, x=None, series=0, plotid=0,
#            track_x=True, track_y=True, do_after=None, track_y_pad=5,
#            aux=False, pad=0.1, **kw):
#
#     xn, yn = self.series[plotid][series]
#
#     plot = self.plots[plotid]
#
#     xd = plot.data.get_data(xn)
#     yd = plot.data.get_data(yn)
#
#     if x is None:
#         try:
#             tg = self.time_generators[plotid]
#         except IndexError:
#             tg = time_generator(self.scan_delays[plotid])
#             self.time_generators.append(tg)
#
#         nx = tg.next()
#     else:
#         nx = x
#
#     ny = float(y)
#     # update raw data
#     #        rx = self.raw_x[plotid][series]
#     #        ry = self.raw_y[plotid][series]
#     #
#     #        self.raw_x[plotid][series] = hstack((rx[MAX_LIMIT:], [nx]))
#     #        self.raw_y[plotid][series] = hstack((ry[MAX_LIMIT:], [ny]))
#
#     dl = self.data_limits[plotid]
#     sd = self.scan_delays[plotid]
#     sw = self.scan_widths[plotid]
#
#     pad = dl * pad
#     #        lim = MAX_LIMIT
#     #         pad = 100
#     #        print lim, nx, ny
#     lim = -dl * sd - 1000
#     new_xd = hstack((xd[lim:], [nx]))
#     new_yd = hstack((yd[lim:], [ny]))
#     #        print new_xd
#     self.cur_max[plotid] = max(self.cur_max[plotid], max(new_yd))
#     self.cur_min[plotid] = min(self.cur_min[plotid], min(new_yd))
#
#     def _record_():
#         if track_x and (self.track_x_min or self.track_x_max) \
#                 or self.force_track_x_flag:
#             ma = new_xd[-1]
#             if not sw:
#                 sd = self.scan_delays[plotid]
#                 mi = ma - dl * sd + pad
#                 if self.force_track_x_flag or \
#                                 ma >= dl * sd - pad:
#
#                     if self.force_track_x_flag:
#                         self.force_track_x_flag = False
#                         ma = dl * sd
#
#                     if not self.track_x_max:
#                         ma = None
#                     else:
#                         ma += pad
#
#                     if not self.track_x_min:
#                         mi = None
#                     else:
#                         mi = max(1, mi)
#             else:
#                 ma = max(ma*1.05, sw)
#                 mi = 0
#                 if ma > sw:
#                     mi = ma-sw
#
#             self.set_x_limits(max_=ma,
#                               min_=mi,
#                               plotid=plotid)
#
#         if track_y and (self.track_y_min[plotid] or self.track_y_max[plotid]):
#             if isinstance(track_y, tuple):
#                 mi, ma = track_y
#                 if ma is None:
#                     ma = self.cur_max[plotid]
#
#                 if mi is None:
#                     mi = self.cur_min[plotid]
#
#             else:
#                 if not self.track_y_max[plotid]:
#                     ma = None
#                 else:
#                     ma = self.cur_max[plotid]
#
#                 if not self.track_y_min[plotid]:
#                     mi = None
#                 else:
#                     mi = self.cur_min[plotid]
#             self.set_y_limits(max_=ma,
#                               min_=mi,
#                               plotid=plotid,
#                               pad=track_y_pad,
#                               force=False
#             )
#
#         if aux:
#             self.add_datum_to_aux_plot((nx, ny), plotid, series)
#         else:
#             plot.data.set_data(xn, new_xd)
#             plot.data.set_data(yn, new_yd)
#             #            self.redraw()
#
#     if do_after:
#         do_after_timer(do_after, _record_)
#     else:
#         _record_()
#
#     return nx
