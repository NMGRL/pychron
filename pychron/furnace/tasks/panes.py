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
from traits.api import Button, Bool
from traitsui.api import View, Item, Readonly, UItem, VGroup, HGroup, EnumEditor, spring, \
    InstanceEditor, ButtonEditor, RangeEditor, Tabbed
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pyface.tasks.traits_task_pane import TraitsTaskPane
from pychron.core.ui.custom_label_editor import CustomLabel
from pychron.core.ui.lcd_editor import LCDEditor
from pychron.envisage.icon_button_editor import icon_button_editor


class ControlPane(TraitsDockPane):
    name = 'Controls'
    id = 'pychron.nmgrlfurnace.controls'

    dump_sample_button = Button('Dump')
    funnel_up_button = Button
    funnel_down_button = Button
    funnel_down_enabled = Bool(True)
    funnel_up_enabled = Bool(False)

    # lower_funnel_button = Button('Lower Funnel')
    # raise_funnel_button = Button('Raise Funnel')

    # def _dump_sample_button_fired(self):
    #     self.model.stage_manager.dump_sample()
    #
    # def _raise_funnel_button_fired(self):
    #     self.model.stage_manager.raise_funnel()
    #
    # def _lower_funnel_button_fired(self):
    #     self.model.stage_manager.lower_funnel()

    def _funnel_up_button_fired(self):
        if self.model.raise_funnel():
            self.funnel_up_enabled = False
            self.funnel_down_enabled = True

    def _funnel_down_button_fired(self):
        if self.model.lower_funnel():
            self.funnel_up_enabled = True
            self.funnel_down_enabled = False

    def _dump_sample_button_fired(self):
        self.model.dump_sample()

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

        # c_grp = VGroup(HGroup(Item('setpoint'),
        #                       UItem('setpoint_readback')),
        #                UItem('setpoint_readback',
        #                      enabled_when='0',
        #                      editor=RangeEditor(mode='slider',
        #                                         low_name='setpoint_readback_min',
        #                                         high_name='setpoint_readback_max')),
        #
        #                label='Controller', show_border=True)
        c_grp = VGroup(Item('setpoint'),
                       VGroup(UItem('setpoint_readback', editor=LCDEditor())),
                       label='Controller', show_border=True)
        d_grp = VGroup(Item('stage_manager.calibrated_position_entry', label='Hole'),
                       Item('stage_manager.sample_linear_holder.position',
                            editor=RangeEditor(mode='slider',
                                               low_name='stage_manager.sample_linear_holder.min_value',
                                               high_name='stage_manager.sample_linear_holder.max_value', )),

                       HGroup(UItem('pane.dump_sample_button',
                                    tooltip='Complete sample dumping procedure'),
                              icon_button_editor('pane.funnel_up_button', 'arrow_up',
                                                 enabled_when='pane.funnel_up_enabled',
                                                 editor_kw={'label': 'Funnel Up'}),
                              icon_button_editor('pane.funnel_down_button', 'arrow_down',
                                                 enabled_when='pane.funnel_down_enabled',
                                                 editor_kw={'label': 'Funnel Down'}),
                              spring),
                       UItem('dumper_canvas', editor=ComponentEditor()),
                       # UItem('pane.lower_funnel_button', enabled_when='stage_manager.funnel.min_limit'),
                       # UItem('pane.raise_funnel_button', enabled_when='stage_manager.funnel.max_limit'),
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
