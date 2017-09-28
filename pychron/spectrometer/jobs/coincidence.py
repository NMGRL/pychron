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
from traits.api import List, HasTraits, Str, Bool, Float, Property
from traitsui.api import View, UItem, TableEditor
# ============= standard library imports ========================
from random import random
from ConfigParser import ConfigParser
import os
import time
# ============= local library imports  ==========================
from traitsui.extras.checkbox_column import CheckboxColumn
from traitsui.table_column import ObjectColumn
from pychron.core.stats.peak_detection import PeakCenterError
from pychron.spectrometer.jobs.peak_center import calculate_peak_center, BasePeakCenter
from pychron.paths import paths


class ResultsView(HasTraits):
    results = List
    clean_results = Property(depends_on='results')

    def _get_clean_results(self):
        return [c for c in self.results if c.enabled]

    def traits_view(self):
        cols = [CheckboxColumn(name='enabled'),
                ObjectColumn(name='name'),
                ObjectColumn(name='old_deflection'),
                ObjectColumn(name='new_deflection')]

        v = View(UItem('results', editor=TableEditor(columns=cols,
                                                     sortable=False)),
                 title='Deflection Results',
                 buttons=['OK', 'Cancel'],
                 kind='livemodal')
        return v


class DeflectionResult(HasTraits):
    name = Str
    enabled = Bool(True)
    new_deflection = Float
    old_deflection = Float

    def __init__(self, name, o, n, *args, **kw):
        super(DeflectionResult, self).__init__(*args, **kw)
        self.name = name
        self.old_deflection = o
        self.new_deflection = n


class Coincidence(BasePeakCenter):
    title = 'Coincidence'
    inform = False

    def __init__(self, *args, **kw):
        super(Coincidence, self).__init__(*args, **kw)
        self.window = 0.015
        self.step_width = 0.0005
        self.percent = 80

    def _reference_detector_default(self):
        self.additional_detectors = [di.name for di in self.detectors[1:]]
        return self.detectors[0].name

    def _post_execute(self):
        """
            calculate all peak centers

            calculate relative shifts to a reference detector. not necessarily the same
            as the reference detector used for setting the magnet
        """
        graph = self.graph
        plot = graph.plots[0]
        time.sleep(0.05)

        # wait for graph to fully update
        time.sleep(0.1)

        # def get_peak_center(i, di):
        def get_peak_center(di):
            try:
                lp = plot.plots[di][0]
            except KeyError:
                lp = plot.plots['*{}'.format(di)][0]

            xs = lp.index.get_data()
            ys = lp.value.get_data()

            cx = None
            if len(xs) and len(ys):
                try:
                    result = calculate_peak_center(xs, ys)
                    cx = result[0][1]
                except PeakCenterError:
                    self.warning('no peak center for {}'.format(di))

            return cx

        spec = self.spectrometer

        centers = {d: get_peak_center(d) for d in self.active_detectors}
        print centers
        ref = self.reference_detector
        post = centers[ref]
        if post is None:
            return

        results = []
        for di in self.active_detectors:
            di = spec.get_detector(di)
            cen = centers[di.name]
            if cen is None:
                continue

            dac_dev = post - cen
            if dac_dev < 0:
                sign = -1
            else:
                sign = 1

            if self.spectrometer.simulation:
                dac_dev = -random()

            if abs(dac_dev) < 0.001:
                self.info('no offset detected between {} and {}'.format(ref, di.name))
                continue

            defl = sign * di.map_dac_to_deflection(abs(dac_dev))
            self.info('{} dac dev. {:0.5f}. converted to deflection voltage {:0.1f}.'.format(di.name, dac_dev, defl))

            curdefl = di.deflection
            newdefl = int(curdefl + defl)
            newdefl = max(0, min(newdefl, self.spectrometer.max_deflection))

            if newdefl >= 0:
                results.append(DeflectionResult(di.name, curdefl, newdefl))

        if not results:
            self.information_dialog('no deflection changes needed')
        else:
            rv = ResultsView(results=results)
            info = rv.edit_traits()
            if info.result:
                config = ConfigParser()
                p = os.path.join(paths.spectrometer_dir, 'config.cfg')
                config.read(p)
                for v in rv.clean_results:
                    config.set('Deflections', v.name, v.new_deflection)
                    det = next((d for d in self.active_detectors if d.lower() == v.name.lower()))
                    det = spec.get_detector(det)
                    det.deflection = v.new_deflection

                with open(p, 'w') as wfile:
                    config.write(wfile)

                self.spectrometer.clear_cached_config()

# ============= EOF =============================================

# class CoincidenceScan(MagnetScan):
# start_mass = 39
# stop_mass = 40
# step_mass = 0.005
# title = 'Coincidence Scan'
# inform = True
#
#     def _reference_detector_changed(self, new):
#         self.additional_detectors = [di.name for di in self.spectrometer.detectors
#                                      if di.name != new]
#
#     def _post_execute(self):
#         """
#             calculate all peak centers
#
#             calculate relative shifts to a reference detector. not necessarily the same
#             as the reference detector used for setting the magnet
#         """
#         graph = self.graph
#         plot = graph.plots[0]
#
#         def get_peak_center(i, di):
#             lp = plot.plots[di.name][0]
#             xs = lp.index.get_data()
#             ys = lp.value.get_data()
#
#             # result = None
#             cx = None
#             if len(xs) and len(ys):
#                 try:
#                     result = calculate_peak_center(xs, ys)
#                     cx = result[0][1]
#                 except PeakCenterError:
#                     self.warning('no peak center for {} {}'.format(di.name, di.isotope))
#             # if result is None or isinstance(result, str):
#             #     self.warning('no peak center for {} {}'.format(di.name, di.isotope))
#             # else:
#             return cx
#
#         spec = self.spectrometer
#         centers = dict([(di.name, get_peak_center(i, di))
#                         for i, di in enumerate(spec.detectors)])
#
#         # calculate relative to AX
#         config = ConfigParser()
#         p = os.path.join(paths.spectrometer_dir, 'config.cfg')
#         config.read(open(p, 'r'))
#
#         ref = self.reference_detector
#         post = centers[ref]
#         if post is None:
#             return
#
#         no_change = True
#         for di in spec.detectors:
#             cen = centers[di.name]
#             if cen is None:
#                 continue
#
#             dac_dev = post - cen
#             if abs(dac_dev) < 0.001:
#                 self.info('no offset detected between {} and {}'.format(ref, di.name))
#                 no_change = True
#                 continue
#
#             no_change = False
#
#             defl = di.map_dac_to_deflection(dac_dev)
#             self.info('{} dac dev. {:0.5f}. converted to deflection voltage {:0.1f}.'.format(di.name, dac_dev, defl))
#
#             curdefl = di.deflection
#             newdefl = int(curdefl + defl)
#             if newdefl > 0:
#                 msg = 'Apply new deflection. {} Current {}. New {}'.format(di.name, curdefl, newdefl)
#                 if self.confirmation_dialog(msg):
#                     # update the config.cfg deflections
#                     config.set('Deflection', di.name, newdefl)
#                     di.deflection = newdefl
#
#         if no_change and self.inform:
#             self.information_dialog('no deflection changes needed')
#         else:
#             config.write(p)
#
#     def _graph_hook(self, do, intensities, **kw):
#         graph = self.graph
#         if graph:
#             spec = self.spectrometer
#             for di, inte in zip(spec.detectors, intensities):
#                 lp = graph.plots[0].plots[di.name][0]
#                 ind = lp.index.get_data()
#                 ind = np.hstack((ind, do))
#                 lp.index.set_data(ind)
#                 #                print inte
#                 val = lp.value.get_data()
#                 val = np.hstack((val, inte))
#                 #                val = val / np.max(val)
#
#                 lp.value.set_data(val)
#
#                 # def _magnet_step_hook(self):
#                 #     spec = self.spectrometer
#             #        spec.magnet.set_dac(di, verbose=False)
#             #        if delay:
#             #            time.sleep(delay)
#             #         intensities = spec.get_intensities()
#             #            debug
#             #         if globalv.communication_simulation:
#             #             inte = peak_generator.next()
#             #             intensities = [0], [inte * 1, inte * 2, inte * 3, inte * 4, inte * 5, inte * 6]
#
#         return intensities
#
#     def _graph_factory(self):
#         g = Graph(window_title='Coincidence Scan',
#                   container_dict=dict(padding=5, bgcolor='lightgray'))
#         g.new_plot(padding=[50, 5, 5, 50],
#                    ytitle='Intensity (fA)',
#                    xtitle='Operating Voltage (V)')
#
#         for di in self.spectrometer.detectors:
#             g.new_series(
#                 name=di.name,
#                 color=di.color)
#
#         return g
#
#     def _reference_detector_default(self):
#         self.additional_detectors = self.detectors[1:]
#         return self.detectors[0]
