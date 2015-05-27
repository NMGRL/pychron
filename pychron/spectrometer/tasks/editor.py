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
from pyface.tasks.traits_editor import TraitsEditor
from traits.api import Button, Instance
from traitsui.api import View, UItem, InstanceEditor, VGroup, HGroup
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.icon_button_editor import icon_button_editor


class ScanEditor(TraitsEditor):
    id = 'pychron.scan'
    model = Instance('pychron.spectrometer.scan_manager.ScanManager')

    def traits_view(self):
        v = View(UItem('graph', style='custom', editor=InstanceEditor()))
        return v



class PeakCenterEditor(ScanEditor):
    model = Instance('pychron.spectrometer.jobs.coincidence_scan.CoincidenceScan')


class CoincidenceEditor(PeakCenterEditor):
    stop_button = Button

    def stop_scan(self):
        self.model.stop()
    stop = stop_scan

    def _stop_button_fired(self):
        self.stop_scan()

    def traits_view(self):
        tgrp = HGroup(icon_button_editor('editor.stop_button', 'stop', tooltip='Stop the current scan'))
        v = View(VGroup(tgrp, UItem('graph', style='custom', editor=InstanceEditor())))
        return v



# ============= EOF =============================================



