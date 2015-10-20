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
from traits.api import Bool, List
from traitsui.api import View, UItem, Item, HGroup, EnumEditor, VGroup
# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.editors.check_list_editor import CheckListEditor
from pychron.spectrometer.ion_optics.peak_center_config import PeakCenterConfig, PeakCenterConfigHandler


class CoincidenceConfigHandler(PeakCenterConfigHandler):
    pass


class CoincidenceConfig(PeakCenterConfig):
    additional_detectors = List
    available_detectors = List
    use_nominal_dac = Bool
    pickle_name = 'coincidence_config.p'

    def _detector_changed(self, new):
        super(CoincidenceConfig, self)._detector_changed(new)
        if new:
            self.available_detectors = [d.name for d in self.detectors if d.name != new.name]

    def traits_view(self):
        rgrp = HGroup(
            Item('detector', editor=EnumEditor(name='detectors')),
            Item('isotope', editor=EnumEditor(name='isotopes')),
            show_border=True, label='Reference')

        dgrp = VGroup(HGroup(Item('use_nominal_dac', label='Use Nominal DAC')),
                      HGroup(Item('use_current_dac',
                                  label='Use Current DAC'),
                             Item('dac', enabled_when='not use_current_dac'),
                             enabled_when='not use_nominal_dac'),
                      show_border=True, label='Center')
        degrp = VGroup(UItem('additional_detectors', style='custom',
                             editor=CheckListEditor(name='available_detectors', cols=len(self.available_detectors))),
                       show_border=True, label='Detectors')

        v = View(VGroup(rgrp, degrp, dgrp),
                 buttons=['OK', 'Cancel'],
                 kind='livemodal',
                 title='Coincidence',
                 handler=CoincidenceConfigHandler())
        return v

# ============= EOF =============================================
