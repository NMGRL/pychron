# ===============================================================================
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
# ===============================================================================

# ============= enthought library imports =======================
from traitsui.api import View, Item, VGroup, InstanceEditor

from pychron.lasers.tasks.laser_panes import ClientPane, BaseLaserPane, \
    StageControlPane, ControlPane, AxesPane, SupplementalPane

# ============= standard library imports ========================
# ============= local library imports  ==========================
class FusionsDiodeClientPane(ClientPane):
    pass

class FusionsDiodePane(BaseLaserPane):
    pass


class FusionsDiodeStagePane(StageControlPane):
    id = 'pychron.fusions.diode.stage'


class FusionsDiodeControlPane(ControlPane):
    id = 'pychron.fusions.diode.control'


class FusionsDiodeAxesPane(AxesPane):
    id = 'pychron.fusions.diode.axes'


class FusionsDiodeSupplementalPane(SupplementalPane):
    id = 'pychron.fusions.diode.supplemental'
    name = 'Diode'
    def traits_view(self):
        v = View(
               VGroup(Item('temperature_controller', style='custom',
                               editor=InstanceEditor(view='control_view'),
                               show_label=False,
                               ),
                      label='Watlow',
#                      show_border = True,
                      ),
                 VGroup(Item('pyrometer', show_label=False, style='custom',
                              ),
#                      show_border = True,
                      label='Pyrometer',

                      ),
                 VGroup(Item('control_module_manager', show_label=False, style='custom',
                             ),
#                      show_border = True,
                      label='ControlModule',

                      ),
                  VGroup(Item('fiber_light', style='custom', show_label=False),
                         label='FiberLight'
                         )
               )
        return v
# ============= EOF =============================================
