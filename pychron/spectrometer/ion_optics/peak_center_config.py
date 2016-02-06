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
from apptools import sweet_pickle as pickle
from traits.api import HasTraits, Str, Bool, Float, List, Instance, Enum, Int
from traitsui.api import View, Item, HGroup, Handler, EnumEditor
# ============= standard library imports ========================
import os
# ============= local library imports  ==========================
from pychron.paths import paths
from pychron.pychron_constants import QTEGRA_INTEGRATION_TIMES
from pychron.spectrometer.base_detector import BaseDetector


class PeakCenterConfigHandler(Handler):
    def closed(self, info, isok):
        if isok:
            info.object.dump()
        return isok


class PeakCenterConfig(HasTraits):
    detectors = List(transient=True)
    detector = Instance(BaseDetector, transient=True)
    detector_name = Str
    isotope = Str('Ar40')
    isotopes = List(transient=True)
    dac = Float
    use_current_dac = Bool(True)
    integration_time = Enum(QTEGRA_INTEGRATION_TIMES)
    directions = Enum('Increase', 'Decrease', 'Oscillate')
    pickle_name = 'peak_center_config.p'
    window = Float(0.015)
    step_width = Float(0.0005)
    min_peak_height = Float(1.0)
    percent = Int(80)

    def _integration_time_default(self):
        return QTEGRA_INTEGRATION_TIMES[4]  # 1.048576

    def dump(self):
        p = os.path.join(paths.hidden_dir, self.pickle_name)
        with open(p, 'wb') as wfile:
            pickle.dump(self, wfile)

    def _detector_changed(self, new):
        if new:
            self.detector_name = new.name

    def traits_view(self):
        v = View(Item('detector', editor=EnumEditor(name='detectors')),
                 Item('isotope', editor=EnumEditor(name='isotopes')),
                 HGroup(Item('use_current_dac',
                             label='Use Current DAC'),
                        Item('dac', enabled_when='not use_current_dac')),
                 Item('integration_time'),
                 Item('directions'),
                 Item('window', label='Peak Width (V)'),
                 Item('step_width', label='Step Width (V)'),
                 Item('min_peak_height', label='Min Peak Height (fA)'),
                 Item('percent'),
                 buttons=['OK', 'Cancel'],
                 kind='livemodal',
                 title='Peak Center',
                 handler=PeakCenterConfigHandler)
        return v
# ============= EOF =============================================
