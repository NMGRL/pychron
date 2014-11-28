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



#=============enthought library imports=======================
from chaco.api import PlotAxis as ScalesPlotAxis
from chaco.scales.api import CalendarScaleSystem, TimeScale
from chaco.scales_tick_generator import ScalesTickGenerator
#=============standard library imports ========================
import time
from numpy import array
#=============local library imports  ==========================
from pychron.core.time_series.time_series import smooth, \
    seasonal_subseries, autocorrelation, downsample_1d

from stacked_graph import StackedGraph
from stream_graph import StreamGraph, StreamStackedGraph
from graph import Graph


HMSScales = [TimeScale(microseconds=100), TimeScale(milliseconds=10)] + \
           [TimeScale(seconds=dt) for dt in (1, 5, 15, 30)] + \
           [TimeScale(minutes=dt) for dt in (5, 15, 30)] + \
           [TimeScale(hours=dt) for dt in (6, 12, 24)] + \
           [TimeScale(days=dt) for dt in (1, 2, 7)
]


class TimeSeriesGraph(Graph):
    def smooth(self, x, **kw):
        return smooth(x, **kw)

    def seasonal_subseries(self, x, y, **kw):
        return seasonal_subseries(x, y, **kw)

    def autocorrelation(self, y, **kw):
        return autocorrelation(y, **kw)

    def downsample(self, x, y, d, plotid=0, series=0):
#        x = self.get_data(plotid, series)
#        y = self.get_data(plotid, series, axis=1)

        self.set_data(downsample_1d(array(x), d), plotid, series)
        self.set_data(downsample_1d(array(y), d), plotid, series, axis=1)
        self.redraw()

#    def _convert_index(self, ind):
#        '''
#            ind is in secs since first epoch
#            convert to a timestamp
#            return a str
#        '''
#        return convert_timestamp(ind)

    def set_x_title(self, t, plotid=0):
        '''
        '''
        axis = self._get_x_axis(plotid)
        axis.title = t
        # print axis.title, axis, t
        super(TimeSeriesGraph, self).set_x_title(t, plotid=plotid)

    def set_axis_label_color(self, *args, **kw):
        '''
        '''
        kw['attr'] = 'title'
        if args[0] == 'x':
            kw['axis'] = self._get_x_axis(kw['plotid'])

        self._set_axis_color(*args, **kw)

    def set_axis_tick_color(self, *args, **kw):
        if args[0] == 'x':
            kw['axis'] = self._get_x_axis(kw['plotid'])
        super(TimeSeriesGraph, self).set_axis_tick_color(*args, **kw)
#        StackedGraph.set_axis_tick_color(self, *args, **kw)

    def _get_x_axis(self, plotid):
        plot = self.plots[plotid]
        # print plot.index_axis.title
        return plot.index_axis
#        for underlay in plot.underlays:
#            if underlay.orientation == 'bottom':
#                #print t,underlay,underlay.title
#
#                return underlay

    def new_plot(self, *args, **kw):
        '''
        '''

        kw['pan'] = 'x' if not 'pan' in kw else kw['pan']

        return super(TimeSeriesGraph, self).new_plot(*args, **kw)

    def new_series(self, x=None, y=None, plotid=0, normalize=False,
                   time_series=True, timescale=False, downsample=None,
                   use_smooth=False, scale=None, ** kw):
        '''
        '''
        if not time_series:
            return super(TimeSeriesGraph, self).new_series(x=x, y=y, plotid=plotid, **kw)

        xd = x
        if x is not None:
            if isinstance(x[0], str):
                # convert the time stamp into seconds since the Epoch
                # Epoch = 12:00 am 1/1/1970
                fmt = "%Y-%m-%d %H:%M:%S"

                args = x[0].split(' +')
                timefunc = lambda xi, fmt: time.mktime(time.strptime(xi, fmt))

                if len(args) > 1:

                    xd = [timefunc(xi.split(' +')[0], fmt) + float(xi.split(' +')[1]) / 1000.0 for xi in x]
                else:
                    fmt = '%a %b %d %H:%M:%S %Y'
                    xd = [timefunc(xi, fmt) for xi in x]

        if downsample:
            xd = downsample_1d(x, downsample)
            y = downsample_1d(y, downsample)

        if use_smooth:
            y = smooth(y)

        if xd is not None:
            xd = array(xd)
            if normalize:
                xd = xd - xd[0]

            if scale:
                xd = xd * scale

        plot, names, rd = self._series_factory(xd, y, plotid=plotid, **kw)
        if 'type' in rd:
            if rd['type'] == 'line_scatter':
                plot.plot(names, type='scatter', marker_size=2,
                                   marker='circle')
                rd['type'] = 'line'

        plota = plot.plot(names, **rd)[0]

#        plota.unified_draw = True
#        plota.use_downsampling = True
        # if the plot is not visible dont remove the underlays
        if plota.visible:
            self._set_bottom_axis(plota, plot, plotid, timescale=timescale)

        return plota, plot

    def _remove_bottom(self, plot):
        title = ''
        for i, underlay in enumerate(plot.underlays):
            try:
                if underlay.orientation == 'bottom':
                    title = underlay.title
                    plot.underlays.pop(i)
            except AttributeError:
                pass

        return title
    def _set_bottom_axis(self, plota, plot, plotid, timescale=False):
        # this is a hack to hide the default plotaxis
        # since a basexyplot's axis cannot be a ScalesPlotAxis (must be instance of PlotAxis)
        # we cant remove the default axis and set the x_axis to the scaled axis
        # also we cant remove the default axis because then we cant change the axis title
        title = self._remove_bottom(plot)
        bottom = self.plotcontainer.stack_order == 'bottom_to_top'
        if bottom:
            if plotid == 0 or timescale:
                axis = ScalesPlotAxis(plota, orientation="bottom",
                                      title=title,
                                      tick_generator=ScalesTickGenerator(scale=CalendarScaleSystem(
                                                                                                   # *HMSScales
                                                                                                   )
                                                                           # scale = TimeScale()
                                                                           )
                                        )


                plot.underlays.append(axis)
        else:
            for pi in self.plots:
                title = self._remove_bottom(pi)

            if (plotid == 0 and len(self.plots) == 1) or plotid == len(self.plots) - 1:
                axis = ScalesPlotAxis(plota, orientation="bottom",
                                  title=title,
                                  tick_generator=ScalesTickGenerator(scale=CalendarScaleSystem(
                                                                                               # *HMSScales
                                                                                               )
                                                                       # scale = TimeScale()
                                                                       )
                                    )


                plot.underlays.append(axis)




class TimeSeriesStackedGraph(TimeSeriesGraph, StackedGraph):
    '''
    '''
    pass


class TimeSeriesStreamGraph(TimeSeriesGraph, StreamGraph):
    '''
    '''
    pass


class TimeSeriesStreamStackedGraph(TimeSeriesGraph, StreamStackedGraph):
    '''
    '''
    pass
#============= EOF ============================================
# def create_dates(numpoints, units = "days"):
#    '''
#            @type units: C{str}
#            @param units:
#    '''
#        """ Returns **numpoints** number of dates that evenly bracket the current
#        date and time.  **units** should be one of "weeks", "days", "hours"
#        "minutes", or "seconds".
#        """
#        units_map = { "weeks" : 7 * 24 * 3600,
#                      "days" : 24 * 3600,
#                      "hours" : 3600,
#                      "minutes" : 60,
#                      "seconds" : 1 }
#        now = time.time()
#        dt = units_map[units]
#        dates = linspace(now, now + numpoints * dt, numpoints)
#        return dates
