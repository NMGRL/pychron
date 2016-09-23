# ===============================================================================
# Copyright 2012 Jake Ross
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
import time

from numpy import max, argmax, vstack, linspace
from scipy import interpolate
from traits.api import Float, Str, Int, List, Enum

from magnet_sweep import MagnetSweep
from pychron.core.helpers.color_generators import colornames
from pychron.core.stats.peak_detection import calculate_peak_center, PeakCenterError
from pychron.core.ui.gui import invoke_in_main_thread
from pychron.graph.graph import Graph


class PeakCenterResult:
    low_dac = None
    center_dac = None
    high_dac = None

    low_signal = None
    center_signal = None
    high_signal = None

    detector = None
    points = None

    def __init__(self, det, pts):
        self.detector = det
        self.points = pts

    @property
    def attrs(self):
        return ('low_dac', 'center_dac', 'high_dac',
                'low_signal', 'center_signal', 'high_signal')


class BasePeakCenter(MagnetSweep):
    title = 'Base Peak Center'
    center_dac = Float
    reference_isotope = Str
    window = Float  # (0.015)
    step_width = Float  # (0.0005)
    min_peak_height = Float(5.0)
    percent = Int
    use_interpolation = False
    interpolation_kind = Enum('linear', 'nearest', 'zero', 'slinear', 'quadratic', 'cubic')
    n_peaks = 1
    select_peak = 1
    use_dac_offset = False
    dac_offset = 0
    calculate_all_peaks = False

    canceled = False
    show_label = False
    result = None
    directions = None

    _markup_idx = 1

    results = List

    def close_graph(self):
        self.graph.close_ui()

    def cancel(self):
        self.canceled = True
        self.stop()

    def get_peak_center(self, ntries=2):

        self._alive = True
        self.canceled = False

        center_dac = self.center_dac
        self.info('starting peak center. center dac= {} step_width={}'.format(center_dac, self.step_width))

        # self.graph = self._graph_factory()

        width = self.step_width
        smart_shift = False
        center = None

        self.debug('width = {}'.format(width))
        for i in range(ntries):
            if not self.isAlive():
                break

            self._reset_graph()

            if i == 0:
                self.graph.add_vertical_rule(self.center_dac, line_style='solid', color='black', line_width=1.5)
            else:
                self.graph.add_vertical_rule(center, line_style='solid', color='black', line_width=1.5)

            start, end = self._get_scan_parameters(i, center, smart_shift)

            center, smart_shift, success = self.iteration(start, end, width)
            if success:
                invoke_in_main_thread(self._post_execute)
                return center

    def get_result(self, detname):
        for i, det in enumerate(self.active_detectors):
            if not isinstance(det, str):
                det = det.name

            if det == detname:
                return self._get_result(i, det)

    def get_results(self):
        results = []
        for i, det in enumerate(self.active_detectors):
            if not isinstance(det, str):
                det = det.name

            result = self._get_result(i, det)
            if result:
                results.append(result)

        return results

    def get_data(self):
        g = self.graph
        data = []
        for i, det in enumerate(self.active_detectors):
            if not isinstance(det, str):
                det = det.name

            xs = g.get_data(series=i)
            ys = g.get_data(series=i, axis=1)

            pts = vstack((xs, ys)).T
            data.append((det, pts))
        return data

    def iteration(self, start, end, width):
        """
            returns center, success (float/None, bool)
        """

        graph = self.graph

        spec = self.spectrometer

        graph.set_x_limits(min_=min([start, end]),
                           max_=max([start, end]))

        def get_reference_intensity():
            keys, signals = spec.get_intensities()
            idx = keys.index(self.reference_detector.name)
            return signals[idx]

        # get the reference detectors current intensity
        cur_intensity = get_reference_intensity()

        # move to start position
        self.info('Moving to starting dac {}'.format(start))
        spec.magnet.set_dac(start)

        tol = cur_intensity * (1 - self.percent / 100.)
        timeout = 10
        self.info('Wait until signal near baseline. tol= {}. timeout= {}'.format(tol, timeout))
        # spec.save_integration()
        # spec.set_integration_time(0.5)

        st = time.time()
        while 1:
            signal = get_reference_intensity()
            if signal < tol:
                self.info('Peak center baseline intensity achieved')
                break

            et = time.time() - st
            if et > timeout:
                self.warning('Peak center failed to move to a baseline position')
                break
            time.sleep(0.5)

        # spec.restore_integration()

        center, smart_shift, success = None, False, False
        # cdd has been tripping during the previous move on obama when moving H1 from 34.5 to 39.7
        # check if cdd is still active
        # if not spec.get_detector_active('CDD'):
        #     self.warning('CDD has tripped!')
        #     self.cancel()
        # else:

        ok = self._do_sweep(start, end, width, directions=self.directions, map_mass=False)
        self.debug('result of _do_sweep={}'.format(ok))

        # wait for graph to fully update
        time.sleep(0.1)

        if ok and self.directions != 'Oscillate':
            if not self.canceled:
                dac_values = graph.get_data()
                intensities = graph.get_data(axis=1)

                result = self._calculate_peak_center(dac_values, intensities)
                self.debug('result of _calculate_peak_center={}'.format(result))
                self.result = result
                if result is not None:
                    xs, ys, mx, my = result

                    center, success = xs[1], True
                    invoke_in_main_thread(self._plot_center, xs, ys, mx, my, center)

                    if self.calculate_all_peaks:
                        self.results = self.get_results()

                else:
                    if max(intensities) > self.min_peak_height * 5:
                        smart_shift = True

                    idx = argmax(intensities)
                    center, success = dac_values[idx], False

        if self.use_dac_offset:
            center += self.dac_offset
        return center, smart_shift, success

    # private
    def _get_result(self, i, det):
        # ys = self.graph.get_data(series=i, axis=1)

        xs = self.graph.get_data(series=i)
        ys = getattr(self.graph.plots[0], 'odata{}'.format(i))

        if xs.shape == ys.shape:
            pts = vstack((xs, ys)).T
            result = PeakCenterResult(det, pts)

            p = self._calculate_peak_center(xs, ys)
            if p:
                [lx, cx, hx], [ly, cy, hy], mx, my = p
                result.low_dac = lx
                result.center_dac = cx
                result.high_dac = hx

                result.low_signal = ly
                result.center_signal = cy
                result.high_signal = hy
            return result

    def _get_scan_parameters(self, i, center_dac, smart_shift):
        wnd = self.window
        scalar = 1
        if smart_shift:
            i = 0
        else:
            if center_dac is None:
                center_dac = self.center_dac
            else:
                scalar = 0.1

        d = wnd * (i * scalar + 1)
        start = center_dac - d
        self.debug('get scan parameters. half-width={},window={}, i={}, scalar={}'.format(d, wnd, i, scalar))
        end = center_dac + d

        dev = abs(start - end)
        self.info(
            'Scan parameters center={:0.5f} width={:0.5f} ({:0.5f} - {:0.5f})'.format(center_dac, dev, start, end))
        return start, end

    def _plot_center(self, xs, ys, mx, my, center):
        graph = self.graph

        s1 = len(graph.series[0])
        graph.new_series(type='scatter', marker='circle',
                         marker_size=4,
                         color='green')

        graph.new_series(type='scatter', marker='circle',
                         marker_size=4,
                         color='orange')

        graph.set_data(xs, series=s1)
        graph.set_data(ys, series=s1, axis=1)

        if self.use_interpolation:
            for i, det in enumerate(self.active_detectors):
                xs = graph.get_data(series=i)
                ys = graph.get_data(series=i, axis=1)

                x, y = self._interpolate(xs, ys)
                graph.new_series(x, y, line_width=1, color=colornames[i])

        graph.set_data([mx], series=s1 + 1)
        graph.set_data([my], series=s1 + 1, axis=1)

        graph.add_vertical_rule(center)

        if self.use_dac_offset:
            l = graph.add_vertical_rule(center + self.dac_offset, color='blue', add_move_tool=True)
            self._offset_rule = l

        graph.redraw()

    def _interpolate(self, x, y):
        f = interpolate.interp1d(x, y, kind=self.interpolation_kind)
        x = linspace(x.min(), x.max(), 500)
        y = f(x)
        return x, y

    def _calculate_peak_center(self, x, y):
        if self.use_interpolation:
            x, y = self._interpolate(x, y)
        if self.n_peaks > 1:
            self.warning('peak deconvolution disabled')
            # def res(p, y, x):
            #     yfit = None
            #     n = p.shape[0] / 3
            #     for h, m, s in p.reshape(n, 3):
            #         yi = h * norm.pdf(x, m, s)
            #         if yfit is None:
            #             yfit = yi
            #         else:
            #             yfit += yi
            #     err = y - yfit
            #     return err
            #
            # mm = x[y.argmax()]
            # counter = range(self.n_peaks)
            # p = [(1, mm, 1) for _ in counter]
            # plsq = leastsq(res, p, args=(y, x))
            #
            # centers = plsq[0]
            # for i in counter:
            #     c = centers[1 + 3 * i]
            #     self.graph.add_vertical_rule(c, color='blue')
            #
            # return c[1 + 3 * (self.select_peak - 1)]

        try:
            result = calculate_peak_center(x, y,
                                           min_peak_height=self.min_peak_height,
                                           percent=self.percent)
            return result
        except PeakCenterError, e:
            self.warning('Failed to find a valid peak. {}'.format(e))

    # ===============================================================================
    # factories
    # ===============================================================================
    def _reset_graph(self):
        self.graph.clear(clear_container=True)
        self._graph_factory(self.graph)

    def _graph_factory(self, graph=None):
        if graph is None:
            graph = Graph(
                window_title=self.title,
                container_dict=dict(padding=5,
                                    bgcolor='lightgray'))

        graph.new_plot(
            padding=[50, 5, 5, 50],
            xtitle='DAC (V)',
            ytitle='Intensity (fA)',
            zoom=False,
            show_legend='ul',
            legend_kw=dict(
                font='modern 8',
                line_spacing=1))

        kind = 'line'
        if self.use_interpolation:
            kind = 'scatter'

        self._series_factory(graph, kind=kind)

        graph.set_series_label('*{}'.format(self.reference_detector.name))
        self._markup_idx = 1
        spec = self.spectrometer
        for di in self.additional_detectors:
            det = spec.get_detector(di)
            c = det.color
            self._series_factory(graph, line_color=c, kind='scatter')
            graph.set_series_label(di)

        if self.show_label:
            graph.add_plot_label('{}@{}'.format(self.reference_isotope,
                                                self.reference_detector), hjustify='center')
        return graph


class PeakCenter(BasePeakCenter):
    title = 'Peak Center'

# ============= EOF =============================================
