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
from numpy import hstack, array, Inf
from traits.api import DelegatesTo, List, Bool, Any
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.ui.gui import invoke_in_main_thread
from pychron.spectrometer.jobs.spectrometer_task import SpectrometerTask


def oscillate():
    flag = True
    while 1:
        if flag:
            yield 1
        else:
            yield -1
        flag = not flag


def alternate(s, e, step, reverse=False):
    i = 0
    j = 0
    flag = True
    if reverse:
        flag = False

    while 1:
        if flag:
            v = s + step * i
            i += 1
            if v >= e:
                break
        else:
            v = e - (step * j)
            j += 1
            if v <= s:
                break
        flag = not flag

        yield v


class BaseSweep(SpectrometerTask):
    detectors = DelegatesTo('spectrometer')
    integration_time = DelegatesTo('spectrometer')

    reference_detector = Any
    additional_detectors = List

    verbose = False
    normalize = Bool(True)

    testing = False

    @property
    def active_detectors(self):
        return [self.reference_detector] + self.additional_detectors

    # private
    def _series_factory(self, graph, kind='line', **kw):
        if 'line_width' not in kw:
            kw['line_width'] = 2

        if kind == 'scatter':
            kw['type'] = 'scatter'
            kw['marker'] = 'circle'
            kw['marker_size'] = 1.5

        graph.new_series(**kw)
        self._markup_idx += 1

    def _test_sweep(self, s, e, step):
        forward = self._calc_step_values(s, e, step)
        backward = self._calc_step_values(e, s, step)
        if not self._sweep(forward):
            return

        self._series_factory(self.graph, kind='scatter')
        if not self._sweep(backward, series=1):
            return

        # alt = alternate(s, e, step)
        # self._series_factory(self.graph)

        # self._sweep(alt, series=2, set_limits=False)
        return True

    def _do_sweep(self, sm, em, stm, directions=None):
        self.debug('_do_sweep sm= {}, em= {}, stm= {}'.format(sm, em, stm))

        if self.testing:
            return self._test_sweep(sm, em, stm)

        if directions is None:
            directions = [1]
        elif isinstance(directions, str):
            if directions == 'Decrease':
                directions = [-1]
            elif directions == 'Oscillate':
                directions = oscillate()
            else:
                directions = [1]

        osm, oem = sm, em
        for di in directions:
            if not self._alive:
                return

            if di == -1:
                sm, em = oem, osm
            else:
                sm, em = osm, oem

            values = self._calc_step_values(sm, em, stm)
            if not self._sweep(values):
                return

        return True

    def _sweep(self, values, series=0, set_limits=True):
        if set_limits:
            self.graph.set_x_limits(values[0], values[-1])

        if self.spectrometer.simulation:
            self._make_pseudo(values)
            self.integration_time = 0.065536

        for v in values:
            if self._alive:
                self._step(v)
                intensity = self._step_intensity()
                invoke_in_main_thread(self._graph_hook, v, intensity, series)

        return self._alive

    def _post_execute(self):
        self.debug('sweep finished')

    def _make_pseudo(self, values):
        pass

    def _step(self, v):
        raise NotImplementedError

    def _step_intensity(self):
        spec = self.spectrometer
        ds = [str(self.reference_detector.name)] + self.additional_detectors
        intensity = spec.get_intensity(ds)

        return intensity

    def _graph_hook(self, di, intensity, series, **kw):
        graph = self.graph
        if graph:
            plot = graph.plots[0]
            if self.testing:
                self._update_graph_data2(plot, di, intensity[0], series)
            else:
                self._update_graph_data(plot, di, intensity)

    def _update_graph_data2(self, plot, di, intensity, series):
        oys = None
        k = 'odata{}'.format(series)
        if hasattr(plot, k):
            oys = getattr(plot, k)

        oys = array([intensity]) if oys is None else hstack((oys, intensity))
        setattr(plot, k, oys)

        data = plot.data
        xs = data.get_data('x{}'.format(series))
        xs = hstack((xs, di))

        data.set_data('x{}'.format(series), xs)
        data.set_data('y{}'.format(series), oys)
        mi, ma = min(oys), max(oys)

        self.graph.set_y_limits(min_=mi, max_=ma, pad='0.05',
                                pad_style='upper')

    def _update_graph_data(self, plot, di, intensity, **kw):
        """
            add and scale scans
        """

        def set_data(k, v):
            plot.data.set_data(k, v)

        def get_data(k):
            return plot.data.get_data(k)

        R = None
        r = None
        mi, ma = Inf, -Inf
        for i, v in enumerate(intensity):
            oys = None
            k = 'odata{}'.format(i)
            if hasattr(plot, k):
                oys = getattr(plot, k)

            oys = array([v]) if oys is None else hstack((oys, v))
            setattr(plot, k, oys)

            if self.normalize:
                if i == 0:
                    # calculate ref range
                    miR = min(oys)
                    maR = max(oys)
                    R = maR - miR
                else:
                    mir = min(oys)
                    mar = max(oys)
                    r = mar - mir

                if r and R:
                    oys = (oys - mir) * R / r + miR

            xs = get_data('x{}'.format(i))
            xs = hstack((xs, di))

            set_data('x{}'.format(i), xs)
            set_data('y{}'.format(i), oys)
            mi, ma = min(mi, min(oys)), max(ma, max(oys))

        self.graph.set_y_limits(min_=mi, max_=ma, pad='0.05',
                                pad_style='upper')

    def _reference_detector_default(self):
        return self.detectors[0]

# ============= EOF =============================================
