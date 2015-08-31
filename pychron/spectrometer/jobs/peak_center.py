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
from traits.api import Float, Str, Int
# ============= standard library imports ========================
import time
from numpy import max, argmax
# ============= local library imports  ==========================
from magnet_sweep import MagnetSweep
from pychron.graph.graph import Graph
from pychron.core.stats.peak_detection import calculate_peak_center, PeakCenterError
from pychron.core.ui.gui import invoke_in_main_thread


class BasePeakCenter(MagnetSweep):
    title = 'Base Peak Center'
    center_dac = Float
    reference_isotope = Str
    window = Float  # (0.015)
    step_width = Float  # (0.0005)
    min_peak_height = Float  # (1.0)
    percent = Int
    canceled = False
    show_label = False
    result = None
    directions = None

    _markup_idx = 1

    def close_graph(self):
        self.graph.close_ui()

    def cancel(self):
        self.canceled = True
        self.stop()

    def get_peak_center(self, ntries=2):

        self._alive = True
        self.canceled = False

        center_dac = self.center_dac
        self.info('starting peak center. center dac= {}'.format(center_dac))

        self._graph_factory()
        # invoke_in_main_thread(self._graph_factory, graph=graph)

        width = self.step_width
        try:
            if self.simulation:
                width = 0.001
        except AttributeError:
            width = 0.001

        smart_shift = False
        center = None
        for i in range(ntries):
            if not self.isAlive():
                break

            if i > 0:
                self._graph_factory()
                # invoke_in_main_thread(self._graph_factory, graph=graph)
            if i==0:
                rule = self.graph.add_vertical_rule(self.center_dac, line_style='solid', color='black', line_width=1.5)
            else:
                rule.value = center

            start, end = self._get_scan_parameters(i, center, smart_shift)

            center, smart_shift, success = self.iteration(start, end, width)
            if success:
                invoke_in_main_thread(self._post_execute)
                return center

    def iteration(self, start, end, width):
        """
            returns center, success (float/None, bool)
        """
        graph = self.graph
        spec = self.spectrometer

        # invoke_in_main_thread(graph.set_x_limits,
        #                       min_=min([start, end]),
        #                       max_=max([start, end]))
        graph.set_x_limits(min_=min([start, end]),
                           max_=max([start, end]))

        # move to start position
        self.info('Moving to starting dac {}'.format(start))
        spec.magnet.set_dac(start)

        tol = 50
        timeout = 10
        self.info('Wait until signal near baseline. tol= {}. timeout= {}'.format(tol, timeout))
        spec.save_integration()
        spec.set_integration_time(0.5)

        st = time.time()
        while 1:
            keys, signals = spec.get_intensities()
            idx = keys.index(self.reference_detector)
            signal = signals[idx]
            if signal < tol:
                self.info('Peak center baseline intensity achieved')
                break

            et = time.time() - st
            if et > timeout:
                self.warning('Peak center failed to move to a baseline position')
                break
            time.sleep(0.5)

        spec.restore_integration()

        # self.info('moving to starting dac {}. delay {} before continuing'.format(start, delay))
        # delay = 3
        # time.sleep(delay)

        center, smart_shift, success = None, False, False
        # cdd has been tripping during the previous move on obama when moving H1 from 34.5 to 39.7
        # check if cdd is still active
        if not spec.get_detector_active('CDD'):
            self.warning('CDD has tripped!')
            self.cancel()
        else:

            ok = self._do_sweep(start, end, width, directions=self.directions, map_mass=False)
            self.debug('result of _do_sweep={}'.format(ok))

            if ok and self.directions != 'Oscillate':
                if not self.canceled:
                    dac_values = graph.get_data()
                    intensities = graph.get_data(axis=1)

                    # n = sorted(zip(dac_values, intensities), key=lambda x: x[0])
                    # dac_values, intensities = zip(*n)

                    result = self._calculate_peak_center(dac_values, intensities)
                    self.debug('result of _calculate_peak_center={}'.format(result))
                    self.result = result
                    if result is not None:
                        xs, ys, mx, my = result

                        center, success = xs[1], True
                        invoke_in_main_thread(self._plot_center, xs, ys, mx, my, center)
                    else:
                        if max(intensities) > self.min_peak_height * 5:
                            smart_shift = True

                        idx = argmax(intensities)
                        center, success = dac_values[idx], False

        return center, smart_shift, success

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

        graph.new_series(type='scatter', marker='circle',
                         marker_size=4,
                         color='green')
        graph.new_series(type='scatter', marker='circle',
                         marker_size=4,
                         color='green')

        graph.set_data(xs, series=self._markup_idx)
        graph.set_data(ys, series=self._markup_idx, axis=1)

        graph.set_data([mx], series=self._markup_idx + 1)
        graph.set_data([my], series=self._markup_idx + 1, axis=1)

        graph.add_vertical_rule(center)
        graph.redraw()

    def _calculate_peak_center(self, x, y):
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
    def _graph_factory(self):
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

        self._series_factory(graph)

        graph.set_series_label('*{}'.format(self.reference_detector))
        self._markup_idx = 1
        spec = self.spectrometer
        for di in self.additional_detectors:
            det = spec.get_detector(di)
            c = det.color
            self._series_factory(graph, line_color=c)
            # graph.new_series(line_color=c)
            graph.set_series_label(di)
            # self._markup_idx += 1

        # graph.new_series(type='scatter', marker='circle',
        #                  marker_size=4,
        #                  color='green')
        # graph.new_series(type='scatter', marker='circle',
        #                  marker_size=4,
        #                  color='green')

        if self.show_label:
            graph.add_plot_label('{}@{}'.format(self.reference_isotope,
                                                self.reference_detector), hjustify='center')
        return graph




class PeakCenter(BasePeakCenter):
    title = 'Peak Center'

# ============= EOF =============================================
# '''
# center pos needs to be ne axial dac units now
# '''
# if isinstance(center_pos, str):
#            '''
#                passing in a mol weight key ie Ar40
#                get_dac_for_mass can take a str or a float
#                if str assumes key else assumes mass
#            '''
#            center_pos = self.magnet.get_dac_for_mass(center_pos)
#
#        if center_pos is None:
#            #center at current position
#            center_dac = self.magnet.read_dac()
#            if isinstance(center_dac, str) and 'ERROR' in center_dac:
#                center_dac = 6.01
#        else:
#            center_dac = center_pos

#        ntries = 2
#        success = False
#        result = None
