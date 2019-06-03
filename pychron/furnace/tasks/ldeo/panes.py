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

from enable.component_editor import ComponentEditor
from pyface.tasks.traits_dock_pane import TraitsDockPane
from pyface.tasks.traits_task_pane import TraitsTaskPane
from traits.api import Button, Bool, Int, Float
from traitsui.api import View, Item, UItem, VGroup, HGroup, spring, \
    Tabbed

from pychron.core.ui.lcd_editor import LCDEditor
from pychron.envisage.icon_button_editor import icon_button_editor


class ControlPane(TraitsDockPane):
    name = 'Controls'
    id = 'pychron.ldeofurnace.controls'

    extract_value = Float
    extract_button = Button('Extract')

    dump_sample_number = Int
    dump_sample_button = Button('Dump')
    # jitter_button = Button
    # jitter_label = Str('Start')
    # jittering = Bool
    # configure_jitter_button = Button

    # refresh_states_button = Button('Refresh')

    set_home_button = Button('Set Home')
    toggle_advanced_view_button = Button
    _advanced_view_state = Bool(False)

    disable_button = Button

    motor_stop_button = Button

    clear_sample_states_button = Button('Clear Dumped Samples')

    def _motor_stop_button_fired(self):
        self.model.stop_motors()

    def _set_home_button_fired(self):
        self.model.furnace_maset_home()

    def _disable_button_fired(self):
        self.model.stop_motors()  # just refers to motor stop function for now

    def _dump_sample_button_fired(self):
        self.model.drop_sample(self.dump_sample_number)

    def _extract_button_fired(self):
        self.model.extract(self.extract_value, 'percent')

    # def _jitter_button_fired(self):
    #     if not self.jittering:
    #         self.model.start_jitter_feeder()
    #         self.jitter_label = 'Stop'
    #     else:
    #         self.model.stop_jitter_feeder()
    #         self.jitter_label = 'Start'
    #     self.jittering = not self.jittering
    #
    # def _configure_jitter_button_fired(self):
    #     self.model.configure_jitter_feeder()

    def _toggle_advanced_view_button_fired(self):
        self._advanced_view_state = not self._advanced_view_state

    def _refresh_states_button_fired(self):
        self.model.refresh_states()

    def _clear_sample_states_button_fired(self):
        self.model.clear_sample_states()

    def trait_context(self):
        return {'object': self.model,
                'pane': self,
                'manager': self.model}

    def traits_view(self):

        c_grp = VGroup(
                       # HGroup(Item('setpoint'),
                       #        UItem('water_flow_state', editor=LEDEditor(label='H2O Flow')),
                       #        spring, icon_button_editor('pane.disable_button', 'cancel')),
                       VGroup(UItem('output_percent_readback', editor=LCDEditor())),
                       icon_button_editor('start_record_button', 'media-record',
                                          tooltip='Start recording',
                                          enabled_when='not _recording'),
                       icon_button_editor('stop_record_button',
                                          'media-playback-stop',
                                          tooltip='Stop recording',
                                          enabled_when='_recording'),
                       label='Controller', show_border=True)

        power_grp = HGroup(UItem('pane.extract_value',
                                width=50,
                                enabled_when='furnace_enabled',
                                tooltip='Power setting for furnace (0-100%)'),
                          UItem('pane.extract_button',
                                enabled_when='furnace_enabled',
                                tooltip='Send the value to the furnace'),
                          show_border=True, label='Furnace Power')

        # jitter_grp = HGroup(UItem('pane.jitter_button', editor=ButtonEditor(label_value='pane.jitter_label')),
        #                     icon_button_editor('pane.configure_jitter_button', 'cog', tooltip='Configure Jitter'),
        #                     show_border=True, label='Jitter')

        dump_grp = HGroup(UItem('pane.dump_sample_number',
                                width=50,
                                enabled_when='dump_sample_enabled',
                                tooltip='Sample number to dump'),
                          UItem('pane.dump_sample_button',
                                enabled_when='dump_sample_enabled',
                                tooltip='Execute the complete sample loading procedure'),
                          UItem('pane.clear_sample_states_button'),
                          show_border=True, label='Dump')
        # status_grp = HGroup(CustomLabel('status_txt', size=14))
        d1 = VGroup(
                    power_grp, dump_grp)
        d2 = VGroup(
            # UItem('pane.refresh_states_button'),
            UItem('dumper_canvas', editor=ComponentEditor()))
        d_grp = HGroup(d1, d2, label='Dumper', show_border=True)

        # v_grp = VGroup(UItem('video_canvas', editor=VideoComponentEditor()),
        #                visible_when='video_enabled',
        #                label='Camera')

        g_grp = VGroup(Item('graph_scan_width', label='Scan Width (mins)'),
                       HGroup(Item('graph_scale', label='Scale'),
                              Item('graph_y_auto', label='Autoscale Y'),
                              Item('graph_ymax', label='Max', format_str='%0.3f', enabled_when='not graph_y_auto'),
                              Item('graph_ymin', label='Min', format_str='%0.3f', enabled_when='not graph_y_auto')),
                       HGroup(icon_button_editor('clear_button', 'clear',
                                                 tooltip='Clear and reset graph'), spring),
                       HGroup(icon_button_editor('start_record_button', 'media-record',
                                                 tooltip='Start recording',
                                                 enabled_when='not _recording'),
                              icon_button_editor('stop_record_button',
                                                 'media-playback-stop',
                                                 tooltip='Stop recording',
                                                 enabled_when='_recording'),
                              icon_button_editor('add_marker_button', 'flag',
                                                 enabled_when='_recording'),
                              show_border=True,
                              label='Record Scan'),
                       label='Graph')
        v = View(VGroup(c_grp,
                        HGroup(Tabbed(d_grp, g_grp))))
        return v


class FurnacePane(TraitsTaskPane):
    def trait_context(self):
        return {'object': self.model,
                'pane': self,
                'manager': self.model}

    def traits_view(self):
        canvas_grp = VGroup(
            # HGroup(UItem('stage_manager.stage_map_name', editor=EnumEditor(name='stage_manager.stage_map_names')),
            #        spring),
            UItem('canvas', style='custom', editor=ComponentEditor()))

        v = View(VGroup(UItem('graph', style='custom'), canvas_grp))
        return v


# ============= EOF =============================================
