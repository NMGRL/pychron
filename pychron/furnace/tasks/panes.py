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
from traits.api import Button
from traitsui.api import View, Item, Readonly, UItem, VGroup, HGroup, EnumEditor, spring, InstanceEditor, ButtonEditor
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pyface.tasks.traits_task_pane import TraitsTaskPane
from pychron.core.ui.custom_label_editor import CustomLabel


class FurnacePane(TraitsTaskPane):
    dump_sample_button = Button('Dump')

    def trait_context(self):
        return {'object': self.model,
                'pane': self,
                'tray_manager': self.model.stage_manager.tray_calibration_manager,
                'stage_manager': self.model.stage_manager}

    def _dump_sample_button_fired(self):
        self.model.dump_sample()

    def traits_view(self):
        canvas_grp = VGroup(
            HGroup(UItem('stage_manager.stage_map_name', editor=EnumEditor(name='stage_manager.stage_map_names')),
                   spring),
            UItem('stage_manager.canvas', style='custom', editor=ComponentEditor()))

        cali_grp = VGroup(
            # Item('tray_manager.style', show_label=False, enabled_when='not tray_manager.isCalibrating()'),
            UItem('tray_manager.calibrate',
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
                        height=75, width=300))

        v = View(VGroup(Item('setpoint'),
                        Readonly('setpoint_readback'),
                        Item('stage_manager.calibrated_position_entry'),
                        UItem('pane.dump_sample_button'),
                        cali_grp,
                        canvas_grp))
        return v

# ============= EOF =============================================
