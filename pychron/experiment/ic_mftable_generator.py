# ===============================================================================
# Copyright 2014 Jake Ross
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
import csv
from traits.api import HasTraits, Button, Any, Instance
from traitsui.api import View, Item
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.loggable import Loggable
from pychron.paths import paths


class ICMFTableGenerator(Loggable):
    spectrometer = Any
    ion_optics_manager = Instance('pychron.spectrometer.ion_optics_manager.IonOpticsManager')

    def make_mftable(self, detectors, refiso):
        """
            peak center `refiso` for each detector in detectors
        :return:
        """
        ion = self.ion_optics_manager
        self.info('Making IC MFTable')
        results = []
        for di in detectors:
            self.info('Peak centering {}@{}'.format(di, refiso))
            ion.setup_peak_center(detector=[di], isotope=refiso)
            ion.do_peak_center(new_thread=False, save=False, warn=False)
            pc = ion.peak_center_result
            if pc:
                self.debug('Peak Center {}@{}={:0.6f}'.format(di, refiso, pc))
                results.append(pc)
            else:
                return False

        self._write_table(detectors, refiso, results)
        return True

    def _write_table(self, detectors, refiso, results):
        p = paths.ic_mftable
        self.info('Writing new IC MFTable to {}'.format(p))
        with open(p, 'w') as fp:
            w = csv.writer(fp)
            header = ['iso'] + detectors
            w.writerow(header)

            w.writerow([refiso] + results)


# ============= EOF =============================================



