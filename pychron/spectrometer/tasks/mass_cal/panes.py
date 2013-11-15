#===============================================================================
# Copyright 2013 Jake Ross
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
from pyface.tasks.traits_dock_pane import TraitsDockPane
from traits.api import HasTraits
from traitsui.api import View, Item, UItem, EnumEditor, TableEditor

#============= standard library imports ========================
#============= local library imports  ==========================
from traitsui.table_column import ObjectColumn


class MassCalibrationTablePane(TraitsDockPane):
    name = 'Calibration Points'
    id = 'pychron.mass_calibration.cal_points'

    def traits_view(self):
        cols = [ObjectColumn(name='isotope',
                             editor=EnumEditor(name='isotopes')),
                ObjectColumn(name='dac')]
        return View(
            UItem('object.scanner.calibration_peaks',
                  editor=TableEditor(columns=cols,
                                     selected='object.scanner.selected')
            )

        )


class MassCalibrationsPane(TraitsDockPane):
    name = 'Calibrations'
    id = 'pychron.mass_calibration.calibrations'

    def traits_view(self):
        return View()


class MassCalibrationControlPane(TraitsDockPane):
    name = 'Controls'
    id = 'pychron.mass_calibration.controls'

    def traits_view(self):
        v = View(UItem('scanner', style='custom'))
        return v

        #============= EOF =============================================
