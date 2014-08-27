#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
from traits.api import HasTraits
# from traitsui.api import View, Item, TableEditor
#============= standard library imports ========================
import os
import time
import numpy as np
#============= local library imports  ==========================
from pychron.graph.regression_graph import RegressionGraph
from pychron.paths import paths
from pychron.core.helpers.filetools import unique_dir
from pychron.graph.graph import Graph
from pychron.core.ui.gui import invoke_in_main_thread
class DeflectionCalibraiton(HasTraits):
    def do_calibration(self):
        self.info('Deflection Calibration')
        self._alive = True
#        for det , mass in [('H2', 'Ar38'), ('H1', 'Ar39'), ('AX', 'Ar40'), ('L1', 41), ('L2', 42)]:
#        for det , mass in [('H2', 'Ar38'), ('H1', 'Ar39'), ('AX', 'Ar40'), ('L1', 41), ('L2', 42)]:
#        for det , mass in [('L1', 'PM41'), ('H2', 'Ar38')]:#, ('L1', 40.9), ('L2', 41.8)]:
        # for det, mass in [('H2', 'Ar38')]:
        for det, mass in [('CDD', 'Ar39')]:
            '''
                 use mftable to calculate the nominal center_pos
                 
                 other option is to just find these values using qtegra empirically
                 
                 ie jump to mass 
                 
            '''
            if not self.isAlive():
                break
            self.reference_detector = det
            self.molecular_weight = mass
            self.cup_deflection_calibration(mass)

    def cup_deflection_calibration(self, mass):

        self.info('{} deflection calibration'.format(self.reference_detector))

        rgraph = RegressionGraph(window_x=100,
                                window_y=50)
        rgraph.new_plot()
        rgraph.new_series(yer=[])

        root_dir = unique_dir(os.path.join(paths.data_dir, 'magfield'), '{}_def_calibration'.format(self.reference_detector))
#        if not os.path.exists(root_dir):
#            os.mkdir(root_dir)

        dm = self.data_manager

        p = os.path.join(root_dir, 'defl_vs_dac.csv')
        deflection_frame_key = dm.new_frame(path=p)

        dm.write_to_frame(['Deflection (V)', '40{} DAC'.format(self.reference_detector)],
                          frame_key=deflection_frame_key)

        start = self.dc_start
        stop = self.dc_stop
        width = self.dc_step
        nstep = (stop - start) / width + 1

        npeak_centers = self.dc_npeak_centers
        self.info('Deflection scan parameters start={}, stop={}, stepwidth={}, nstep={}'.format(start, stop, width, nstep))
        self.info('Reference detector {}'.format(self.reference_detector))
        self.info('Peak centers per step n={}'.format(npeak_centers))

        for i, ni in enumerate(np.linspace(start, stop, nstep)):
            if not self.isAlive():
                break
            self.info('Deflection step {} {} (V)'.format(i + 1, ni))
            self._detectors[self.reference_detector].deflection = ni
            ds = []
            for n in range(npeak_centers):
                if not self.isAlive():
                    break
                self.info('Peak center ni = {}'.format(n + 1))

                p = os.path.join(root_dir, 'peak_scan_{:02n}_{:02n}.csv'.format(int(ni), n))
                dm.new_frame(path=p)
                dm.write_to_frame(['DAC (V)', 'Intensity (fA)'])

                graph = Graph(window_title='Peak Centering',
                              window_x=175 + i * 25 + n * 5,
                              window_y=25 + i * 25 + n * 5
                              )

                self.peak_center(graph=graph,
                                  update_mftable=True,
                                  update_pos=False,
                                  center_pos=mass
                                  )

                if self.isAlive():
                    # write scan to file
                    dm.write_to_frame(zip(graph.get_data(), graph.get_data(axis=1)))

                    if npeak_centers > 1:
                        if not self.simulation:
                            time.sleep(1)

                    if self.peak_center_results:
                        d = (ni, self.peak_center_results[0][1])
                        ds.append(self.peak_center_results[0][1])
                        dm.write_to_frame(list(d), frame_key=deflection_frame_key)

                        # write the centering results to the centering file
                        dm.write_to_frame([('#{}'.format(x), y) for x, y in  zip(graph.get_data(series=1), graph.get_data(series=1, axis=1))])

            if self.peak_center_results:
                rgraph.add_datum((ni, np.mean(ds), np.std(ds)))

            if i == 2:
                invoke_in_main_thread(rgraph.edit_traits)

            # delay so we can view graph momonetarily
            if not self.simulation and self.isAlive():
                time.sleep(2)

        self.info('deflection calibration finished')
#============= EOF =============================================
