# ===============================================================================
# Copyright 2017 ross
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
import time

from pychron.loggable import Loggable


# class MFTableGenerator(Loggable):
#     # def make_mftable(self, ion, detectors, refiso, peak_center_config='ic_peakhop'):
#     def make_mftable(self, ion, cfg):
#         """
#             peak center `refiso` for each detector in detectors
#         :return:
#         """
#         self.info('Making IC MFTable')
#         refiso = cfg.isotope
#
#         ion.backup_mftable()
#         for di in cfg.detectors:
#
#             self.info('Peak centering {}@{}'.format(di, refiso))
#             ion.setup_peak_center(detector=[di], isotope=refiso,
#                                   config_name=cfg.peak_center_config.active_item.name,
#                                   show_label=True, use_configuration_dac=False)
#
#             ion.peak_center.update_others = False
#
#             ion.do_peak_center(new_thread=False, save=True, warn=True)
#             apc = ion.adjusted_peak_center_result
#             if apc:
#                 self.info('Peak Center {}@{}={:0.6f}'.format(di, refiso, apc))
#                 # results.append((di, apc))
#                 time.sleep(0.25)
#             else:
#                 return False

    #     magnet = ion.spectrometer.magnet
    #     if update_existing:
    #         self._update_table(magnet, refiso, results)
    #     else:
    #         self._write_table(detectors, refiso, results)
    #
    #     return True
    #
    # def _update_table(self, magnet, refiso, results):
    #     for det, apc in results:
    #         magnet.update_field_table(det, refiso, apc, 'mftable_generator', update_others=False)

# ============= EOF =============================================
