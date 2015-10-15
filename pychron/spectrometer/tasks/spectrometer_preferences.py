# ===============================================================================
# Copyright 2013 Jake Ross
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
from traits.api import Bool, Float, Enum
from traitsui.api import View, Item, VGroup, HGroup
from envisage.ui.tasks.preferences_pane import PreferencesPane
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.tasks.base_preferences_helper import BasePreferencesHelper


class SpectrometerPreferences(BasePreferencesHelper):
    name = 'Spectrometer'
    preferences_path = 'pychron.spectrometer'
    id = 'pychron.spectrometer.preferences_page'
    send_config_on_startup = Bool
    use_local_mftable_archive = Bool
    use_db_mftable_archive = Bool
    confirmation_threshold_mass = Float
    use_detector_safety = Bool
    use_log_events = Bool
    use_vertical_markers = Bool
    auto_open_readout = Bool
    use_default_scan_settings = Bool
    default_isotope = Enum(('Ar40', 'Ar39', 'Ar38', 'Ar37', 'Ar36'))
    default_detector = Enum(('H2', 'H1', 'AX', 'L1', 'L2', 'CDD'))


class SpectrometerPreferencesPane(PreferencesPane):
    model_factory = SpectrometerPreferences
    category = 'Spectrometer'

    def traits_view(self):
        magnet_grp = VGroup(Item('confirmation_threshold_mass',
                                 tooltip='Request confirmation if magnet move is greater than threshold',
                                 label='Confirmation Threshold (amu)'),
                            show_border=True,
                            label='Magnet')
        mf_grp = VGroup(Item('use_local_mftable_archive',
                             tooltip='Archive mftable to a local git repository',
                             label='Local Archive'),
                        Item('use_db_mftable_archive',
                             tooltip='Archive mftable to central database',
                             label='DB Archive'),
                        show_border=True,
                        label='MFTable')
        gen_grp = VGroup(Item('send_config_on_startup',
                              tooltip='Load the spectrometer parameters on startup', ),
                         Item('auto_open_readout',
                              tooltip='Open readout view when Spectrometer plugin starts'))
        scan_grp = VGroup(Item('use_detector_safety',
                               label='Detector Safety',
                               tooltip='Abort magnet moves '
                                       'if move will place an intensity greater than X on the current detector'),
                          Item('use_log_events', label='Event Logging',
                               tooltip='Display events such as valve open/close, magnet moves on Scan graph'),
                          Item('use_vertical_markers', label='Vertical Markers'),
                          HGroup(Item('use_default_scan_settings',
                                      label='Use Defaults'),
                                 Item('default_detector',
                                      label='Detector',
                                      enabled_when='use_default_scan_settings'),
                                 Item('default_isotope',
                                      label='Isotope',
                                      enabled_when='use_default_scan_settings')),
                          label='Scan',
                          show_border=True)

        return View(VGroup(gen_grp, mf_grp, scan_grp, magnet_grp))

# ============= EOF =============================================
