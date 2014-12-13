# ===============================================================================
# Copyright 2012 Jake Ross
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

# ============= enthought library imports =======================
# ============= standard library imports ========================
from ConfigParser import ConfigParser
import os
import numpy as np
# ============= local library imports  ==========================
from pychron.core.stats.peak_detection import PeakCenterError
from pychron.spectrometer.jobs.peak_center import calculate_peak_center
from pychron.paths import paths
from pychron.spectrometer.jobs.magnet_scan import MagnetScan
from pychron.graph.graph import Graph
from pychron.globals import globalv


class CoincidenceScan(MagnetScan):
    start_mass = 39
    stop_mass = 40
    step_mass = 0.005
    title = 'Coincidence Scan'
    inform = True

    def _post_execute(self):
        """
            calculate all peak centers

            calculate relative shifts to a reference detector. not necessarily the same
            as the reference detector used for setting the magnet
        """
        graph = self.graph
        plot = graph.plots[0]
        def get_peak_center(i, di):
            lp = plot.plots[di.name][0]
            xs = lp.index.get_data()
            ys = lp.value.get_data()

            # result = None
            cx = None
            if len(xs) and len(ys):
                try:
                    result = calculate_peak_center(xs, ys)
                    cx = result[0][1]
                except PeakCenterError:
                    self.warning('no peak center for {} {}'.format(di.name, di.isotope))
            # if result is None or isinstance(result, str):
            #     self.warning('no peak center for {} {}'.format(di.name, di.isotope))
            # else:
            return cx

        spec = self.spectrometer
        centers = dict([(di.name, get_peak_center(i, di))
                            for i, di in enumerate(spec.detectors)])

        # calculate relative to AX
        config = ConfigParser()
        p = os.path.join(paths.spectrometer_dir, 'config.cfg')
        config.read(open(p, 'r'))

        ref = 'AX'
        post = centers[ref]
        if post is None:
            return

        no_change = True
        for di in spec.detectors:
            cen = centers[di.name]
            if cen is None:
                continue

            dac_dev = post - cen
            if abs(dac_dev) < 0.001:
                self.info('no offset detected between {} and {}'.format(ref, di.name))
                no_change = True
                continue

            no_change = False

            defl = di.map_dac_to_deflection(dac_dev)
            self.info('{} dac dev. {:0.5f}. converted to deflection voltage {:0.1f}.'.format(di.name, dac_dev, defl))

            curdefl = di.deflection
            newdefl = int(curdefl + defl)
            if newdefl > 0:
                msg = 'Apply new deflection. {} Current {}. New {}'.format(di.name, curdefl, newdefl)
                if self.confirmation_dialog(msg):
                    # update the config.cfg deflections
                    config.set('Deflection', di.name, newdefl)
                    di.deflection = newdefl

        if no_change and self.inform:
            self.information_dialog('no deflection changes needed')
        else:
            config.write(p)

    def _graph_hook(self, do, intensities, **kw):
        graph = self.graph
        if graph:
            spec = self.spectrometer
            for di, inte in zip(spec.detectors, intensities[1]):
                lp = graph.plots[0].plots[di.name][0]
                ind = lp.index.get_data()
                ind = np.hstack((ind, do))
                lp.index.set_data(ind)
#                print inte
                val = lp.value.get_data()
                val = np.hstack((val, inte))
#                val = val / np.max(val)

                lp.value.set_data(val)

    def _magnet_step_hook(self, detector=None, peak_generator=None):
        spec = self.spectrometer
#        spec.magnet.set_dac(di, verbose=False)
#        if delay:
#            time.sleep(delay)
        intensities = spec.get_intensities()
#            debug
        if globalv.experiment_debug:
            inte = peak_generator.next()
            intensities = [0], [inte * 1, inte * 2, inte * 3, inte * 4, inte * 5, inte * 6]

        return intensities

    def _graph_factory(self):
        g = Graph(window_title='Coincidence Scan',
                  container_dict=dict(padding=5, bgcolor='lightgray')
                  )
        g.new_plot(padding=[50, 5, 5, 50],
                   ytitle='Intensity (fA)',
                   xtitle='Operating Voltage (V)')

        for di in self.spectrometer.detectors:
            g.new_series(
                         name=di.name,
                         color=di.color)

        return g


# ============= EOF =============================================
