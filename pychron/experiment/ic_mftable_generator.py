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
import time
from numpy import array, diff
from contextlib import contextmanager

from pychron.loggable import Loggable

ARGON_IC_MFTABLE = True


class ICMFTableGenerator(Loggable):
    def make_mftable(self, arun, detectors, refiso, peak_center_config='ic_peakhop', n=1):
        """
            peak center `refiso` for each detector in detectors
        :return:
        """
        ion = arun.ion_optics_manager
        plot_panel = arun.plot_panel

        def func(x):
            if not x:
                ion.cancel_peak_center()

        @contextmanager
        def listen():
            arun.on_trait_change(func, '_alive')
            yield
            arun.on_trait_change(func, '_alive', remove=True)

        cumulative = {}
        with arun.ion_optics_manager.mftable_ctx('ic_mftable'):
            for i in range(n):
                with listen():
                    self.info('Making IC MFTable')
                    results = []
                    for di in detectors:
                        if not arun.is_alive():
                            return False

                        self.info('Peak centering {}@{}'.format(di, refiso))
                        ion.setup_peak_center(detector=[di], isotope=refiso,
                                              config_name=peak_center_config,
                                              plot_panel=plot_panel, show_label=True, use_configuration_dac=False)

                        arun.peak_center = ion.peak_center
                        ion.do_peak_center(new_thread=False, save=False, warn=False)
                        apc = ion.adjusted_peak_center_result
                        if apc:
                            self.info('Peak Center {}@{}={:0.6f}'.format(di, refiso, apc))
                            results.append((di, apc))
                            time.sleep(0.25)
                        else:
                            return False

                magnet = arun.ion_optics_manager.spectrometer.magnet
                for det, apc in results:
                    if det in cumulative:
                        centers = cumulative[det]
                    else:
                        centers = []

                    centers.append(apc)
                    cumulative[det] = centers
                    magnet.update_field_table(det, refiso, apc, 'ic_generator', update_others=False)

        self.debug('=============== IC Peak Hop Center Deviations ===============')
        for k, v in cumulative.items():
            v = array(v)
            self.debug('{} {} {}'.format(k, v, diff(v)))
        self.debug('=============================================================')
        return True

        # def _update_table(self, arun, refiso, results):
        #     magnet = arun.ion_optics_manager.spectrometer.magnet
        #     for det, apc in results:
        #         magnet.update_field_table(det, refiso, apc, 'ic_generator', update_others=False)

        # def _write_table(self, detectors, refiso, results):
        #     p = paths.ic_mftable
        #     results = [r[1] for r in results]
        #     self.info('Writing new IC MFTable to {}'.format(p))
        #     with open(p, 'w') as wfile:
        #         w = csv.writer(wfile)
        #
        #         w.writerow(['parabolic' if ARGON_IC_MFTABLE else 'discrete'])
        #         header = ['iso'] + list(detectors)
        #         w.writerow(header)
        #         w.writerow([refiso] + results)
        #
        #         # temporary hack to full write the ic mf table
        #         if ARGON_IC_MFTABLE and refiso == 'Ar40' and detectors[0] in ('H1', 'H2'):
        #             row = ['Ar39', results[0] - 0.1]
        #             row.extend(results[1:])
        #
        #             w.writerow(row)
        #
        #             row = ['Ar36', results[0] - 0.4]
        #             row.extend(results[1:])
        #
        #             w.writerow(row)

# ============= EOF =============================================
