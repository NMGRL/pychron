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
from enable.component_editor import ComponentEditor
from pyface.tasks.traits_dock_pane import TraitsDockPane
from traits.api import Button
from traitsui.api import View, Item, Readonly, UItem, UReadonly, VGroup, HGroup, EnumEditor, spring, \
    InstanceEditor, ButtonEditor, RangeEditor, Tabbed
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pyface.tasks.traits_task_pane import TraitsTaskPane
from pychron.core.ui.custom_label_editor import CustomLabel


class ControlPane(TraitsDockPane):
    name = 'Controls'
    id = 'pychron.nmgrlfurnace.controls'

    dump_sample_button = Button('Dump')
    lower_funnel_button = Button('Lower Funnel')
    raise_funnel_button = Button('Raise Funnel')

    def _dump_sample_button_fired(self):
        self.model.stage_manager.dump_sample()

    def _raise_funnel_button_fired(self):
        self.model.stage_manager.raise_funnel()

    def _lower_funnel_button_fired(self):
        self.model.stage_manager.lower_funnel()

    def trait_context(self):
        return {'object': self.model,
                'pane': self,
                'tray_manager': self.model.stage_manager.tray_calibration_manager,
                'stage_manager': self.model.stage_manager}

    def traits_view(self):
        cali_grp = VGroup(UItem('tray_manager.calibrate',
                                enabled_when='stage_manager.stage_map_name',
                                editor=ButtonEditor(label_value='tray_manager.calibration_step')),
                          HGroup(Readonly('tray_manager.x', format_str='%0.3f'),
                                 Readonly('tray_manager.y', format_str='%0.3f')),
                          Readonly('tray_manager.rotation', format_str='%0.3f'),
                          Readonly('tray_manager.scale', format_str='%0.4f'),
                          Readonly('tray_manager.error', format_str='%0.2f'),
                          UItem('tray_manager.calibrator', style='custom', editor=InstanceEditor()),
                          CustomLabel('tray_manager.calibration_help',
                                      color='green',
                                      height=75, width=300),

                          show_border=True, label='Calibration')

        c_grp = VGroup(HGroup(Item('setpoint'),
                              UReadonly('setpoint_readback',
                                        width=100)),
                       UItem('setpoint_readback',
                             enabled_when='0',
                             editor=RangeEditor(mode='slider',
                                                low_name='setpoint_readback_min',
                                                high_name='setpoint_readback_max')),

                       label='Controller', show_border=True)

        d_grp = VGroup(Item('stage_manager.calibrated_position_entry', label='Hole'),
                       Item('stage_manager.dumper.position',
                            editor=RangeEditor(mode='slider',
                                               low_name='stage_manager.dumper.min_value',
                                               high_name='stage_manager.dumper.max_value', )),
                       UItem('pane.lower_funnel_button', enabled_when='stage_manager.funnel.min_limit'),
                       UItem('pane.dump_sample_button', enabled_when='stage_manager.funnel.max_limit'),
                       UItem('pane.raise_funnel_button', enabled_when='stage_manager.funnel.max_limit'),
                       label='Dumper', show_border=True)

        v = View(VGroup(c_grp,
                        HGroup(Tabbed(d_grp, cali_grp))))
        return v


class FurnacePane(TraitsTaskPane):
    def trait_context(self):
        return {'object': self.model,
                'pane': self,
                'tray_manager': self.model.stage_manager.tray_calibration_manager,
                'stage_manager': self.model.stage_manager}

    def traits_view(self):
        canvas_grp = VGroup(
            HGroup(UItem('stage_manager.stage_map_name', editor=EnumEditor(name='stage_manager.stage_map_names')),
                   spring),
            UItem('stage_manager.canvas', style='custom', editor=ComponentEditor()))

        v = View(VGroup(UItem('graph', style='custom'), canvas_grp))
        return v

# ============= EOF =============================================
