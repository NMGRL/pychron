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
from traitsui.api import View, Item, VGroup, \
    HGroup, spring, UItem, ButtonEditor, Group
from pyface.tasks.traits_dock_pane import TraitsDockPane

from pychron.lasers.tasks.laser_panes import BaseLaserPane, ClientPane, \
    StageControlPane, AxesPane, SupplementalPane
from pychron.core.ui.led_editor import LEDEditor

#============= standard library imports ========================
#============= local library imports  ==========================
class FusionsUVClientPane(ClientPane):
    pass


class FusionsUVPane(BaseLaserPane):
    pass


class FusionsUVStagePane(StageControlPane):
    id = 'pychron.fusions.uv.stage'

class FusionsUVAxesPane(AxesPane):
    id = 'pychron.fusions.uv.axes'


class FusionsUVSupplementalPane(SupplementalPane):
    id = 'pychron.fusions.uv.supplemental'
    name = 'UV'
    def traits_view(self):
        v = View(
            Group(
                #VGroup(
                #       Item('mode'),
                #       Item('burst_shot')),
                #                VGroup(Item('temperature_controller', style='custom',
#                                editor=InstanceEditor(view='control_view'),
#                                show_label=False,
#                                ),
#                       label='Watlow',
# #                      show_border = True,
#                       ),
#                  VGroup(Item('pyrometer', show_label=False, style='custom',
#                               ),
# #                      show_border = True,
#                       label='Pyrometer',
#
#                       ),
#                  VGroup(Item('control_module_manager', show_label=False, style='custom',
#                              ),
# #                      show_border = True,
#                       label='ControlModule',
#
#                       ),
VGroup(Item('fiber_light', style='custom', show_label=False),
       label='FiberLight'
),
layout='tabbed')
        )
        return v


def button_editor(name, label, **kw):
    return UItem(name, editor=ButtonEditor(label_value=label))


class FusionsUVControlPane(TraitsDockPane):
    id = 'pychron.fusions.uv.control'

    def traits_view(self):
        grp = VGroup(
            HGroup(
                Item('enabled_led', show_label=False,
                     style='custom', editor=LEDEditor()),
                button_editor('enable', 'enable_label'),
                #button_editor('object.laser_script_executor.execute_button',
                #              'object.laser_script_executor.execute_label'),
                #Item('object.laser_script_executor.names', show_label=False),
                spring
            ),
            #                      Item('execute_button', show_label=False, editor=ButtonEditor(label_value='execute_label')),
            HGroup(
                Item('action_readback', width=100, style='readonly', label='Action'),
                Item('status_readback', style='readonly', label='Status'),
            ),
            HGroup(button_editor('fire_button', 'fire_label'),
                   Item('mode', show_label=False),
                   enabled_when='object.enabled and object.status_readback=="Laser On"'
            ),
            HGroup(
                Item('burst_shot', label='N Burst', enabled_when='mode=="Burst"'),
                Item('reprate', label='Rep. Rate')
            ),
            HGroup(
                Item('burst_readback', label='Burst Rem.', width=50, style='readonly'),
                Item('energy_readback', label='Energy (mJ)',
                     style='readonly', format_str='%0.2f'),
                Item('pressure_readback', label='Pressure (mbar)',
                     style='readonly', width=100, format_str='%0.1f'),
                spring,
                enabled_when='object.enabled'
            ),
#             show_border=True,
#             label='Power'
            )
        v = View(grp)
        return v
#============= EOF =============================================
