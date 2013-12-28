#===============================================================================
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
#===============================================================================



#=============enthought library imports=======================
from pyface.timer.api import do_after as do_after_timer

#=============standard library imports ========================
from numpy import hstack, Inf
#=============local library imports  ==========================
# from pychron.graph.editors.stream_plot_editor import StreamPlotEditor
from pychron.core.helpers.datetime_tools import current_time_generator as time_generator
from stacked_graph import StackedGraph
from graph import Graph

MAX_LIMIT = int(-1 * 60 * 60 * 24)


class StreamGraph(Graph):
    """
    """
    # plot_editor_klass = StreamPlotEditor
    global_time_generator = None

    cur_min = None
    cur_max = None

    #    track_y_max = Bool(True)
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


    def clear(self):
        self.scan_delays = []
        self.time_generators = []
        self.data_limits = []
        self.cur_min = []
        self.cur_max = []
        self.track_x_max = True
        self.track_x_min = True
        self.track_y_max = []
        self.track_y_min = []
        self.force_track_x_flag = False

        super(StreamGraph, self).clear()

    def new_plot(self, **kw):
        '''
        '''
        sd = kw['scan_delay'] if 'scan_delay' in kw else 0.5
        dl = kw['data_limit'] if 'data_limit' in kw else 500

        self.scan_delays.append(sd)
        self.data_limits.append(dl)
        self.cur_min.append(Inf)
        self.cur_max.append(-Inf)

        # self.track_x_max.append(True)
        # self.track_x_min.append(True)
        self.track_y_max.append(True)
        self.track_y_min.append(True)
        # self.force_track_x_flag.append(False)

        args = super(StreamGraph, self).new_plot(**kw)

        self.set_x_limits(min_=0, max_=dl * sd + 1, plotid=len(self.plots) - 1)

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

    def set_scan_delay(self, v, plotid=0):
        self.scan_delays[plotid] = v

    def set_data_limits(self, d, plotid=None):
        if plotid is None:
            for i in range(len(self.scan_delays)):
                self.data_limits[i] = d
        else:
            self.data_limits[plotid] = d

    def set_time_zero(self, plotid=0):

        tg = time_generator(self.scan_delays[plotid])
        try:
            self.time_generators[plotid] = tg
        except IndexError:
            self.time_generators.append(tg)

    def record_multiple(self, ys, plotid=0, scalar=1, track_x=True, **kw):

        tg = self.global_time_generator
        if tg is None:
            tg = time_generator(self.scan_delays[plotid])
            self.global_time_generator = tg

        x = tg.next() * scalar
        for i, yi in enumerate(ys):
            kw['track_x'] = False
            self.record(yi, x=x, series=i, **kw)

        ma = max(ys)
        mi = min(ys)
        if ma < self.cur_max[plotid]:
            self.cur_max[plotid] = -Inf
        if mi > self.cur_min[plotid]:
            self.cur_min[plotid] = Inf

        if track_x:
            dl = self.data_limits[plotid]
            mi = max(1, x - dl * self.scan_delays[plotid])
            self.set_x_limits(# max=x,
                              min_=mi,
                              plotid=plotid,
                              #                          pad=1
            )
        return x

    def record(self, y, x=None, series=0, plotid=0,
               track_x=True, track_y=True, do_after=None, track_y_pad=5,
               aux=False, pad=0.1, **kw):

        xn, yn = self.series[plotid][series]

        plot = self.plots[plotid]

        xd = plot.data.get_data(xn)
        yd = plot.data.get_data(yn)

        if x is None:
            try:
                tg = self.time_generators[plotid]
            except IndexError:
                tg = time_generator(self.scan_delays[plotid])
                self.time_generators.append(tg)

            nx = tg.next()
        else:
            nx = x

        ny = float(y)
        # update raw data
        #        rx = self.raw_x[plotid][series]
        #        ry = self.raw_y[plotid][series]
        #
        #        self.raw_x[plotid][series] = hstack((rx[MAX_LIMIT:], [nx]))
        #        self.raw_y[plotid][series] = hstack((ry[MAX_LIMIT:], [ny]))

        dl = self.data_limits[plotid]
        sd = self.scan_delays[plotid]
        pad = dl * pad
        #        lim = MAX_LIMIT
        #         pad = 100
        #        print lim, nx, ny
        lim = -dl * sd - 1000
        new_xd = hstack((xd[lim:], [nx]))
        new_yd = hstack((yd[lim:], [ny]))
        #        print new_xd
        self.cur_max[plotid] = max(self.cur_max[plotid], max(new_yd))
        self.cur_min[plotid] = min(self.cur_min[plotid], min(new_yd))

        def _record_():
            if track_x and (self.track_x_min or self.track_x_max) \
                or self.force_track_x_flag:
                ma = new_xd[-1]
                sd = self.scan_delays[plotid]
                mi = ma - dl * sd + pad
                if self.force_track_x_flag or \
                                ma >= dl * sd - pad:

                    if self.force_track_x_flag:
                        self.force_track_x_flag = False
                        ma = dl * sd

                    if not self.track_x_max:
                        ma = None
                    else:
                        ma = ma + pad

                    if not self.track_x_min:
                        mi = None
                    else:
                        mi = max(1, mi)

                    self.set_x_limits(max_=ma,
                                      min_=mi,
                                      plotid=plotid,
                                      #                              force=False
                                      #                              pad=10 * self.scan_delays[plotid]
                    )

            if track_y and (self.track_y_min[plotid] or self.track_y_max[plotid]):
                if isinstance(track_y, tuple):
                    mi, ma = track_y
                    if ma is None:
                        ma = self.cur_max[plotid]

                    if mi is None:
                        mi = self.cur_min[plotid]

                else:
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
                                  plotid=plotid,
                                  pad=track_y_pad,
                                  force=False
                )

            if aux:
                self.add_datum_to_aux_plot((nx, ny), plotid, series)
            else:
                plot.data.set_data(xn, new_xd)
                plot.data.set_data(yn, new_yd)
            #            self.redraw()

        if do_after:
            do_after_timer(do_after, _record_)
        else:
            _record_()

        return nx


class StreamStackedGraph(StreamGraph, StackedGraph):
    pass

#============= EOF ====================================
#    def set_x_limits(self, *args, **kw):
#        '''
#            @type *args: C{str}
#            @param *args:
#
#            @type **kw: C{str}
#            @param **kw:
#        '''
#
#        super(StreamGraph, self).set_x_limits(*args, **kw)
# #        pid = kw['plotid']
# #        args = self._get_limits('index', pid)
#
# #        if args is not None:
# #
# #            self.data_limits[pid] = max(args[0], args[1])


#    def record(self, val, series = 0, plotid = 0):
#        '''
#            @type val: C{str}
#            @param val:
#
#            @type series: C{str}
#            @param series:
#
#            @type plotid: C{str}
#            @param plotid:
#
#            @type block_write: C{str}
#            @param block_write:
#        '''
#
#        xn, yn = self.series[plotid][series]
#
#        plot = self.plots[plotid]
#
#        xd = plot.data.get_data(xn)
#        yd = plot.data.get_data(yn)
#
#        if isinstance(val, tuple) or isinstance(val, list):
#            x = float(val[0])
#            y = float(val[1])
#        else:
#            y = val
#            if y is not None:
#                y = float(y)
#
#            x = 0
#            try:
#                tg = self.time_generators[plotid]
#
#            except:
#                tg = time_generator()
#                self.time_generators.append(tg)
#
#            x = tg.next()
#
#        dl = self.data_limits[plotid]
#
#        lim = 0
#        if self.trim_data[plotid]:
#            lim = int(-dl / (self.scan_delays[plotid])) + 1
#
#        if y is not None:
#            new_xd = hstack((xd[lim:], [x]))
#            new_yd = hstack((yd[lim:], [y]))
#        else:
#            if x > dl:
#                lim = 1
#
#            new_xd = xd[lim:]
#            new_yd = yd[lim:]
#
#
#        plot.data.set_data(xn, new_xd)
#        plot.data.set_data(yn, new_yd)
#
#        if x > dl and self.track_x[plotid]:
#            self.set_x_limits(track = dl, plotid = plotid)
#            self.track_x[plotid] = False
