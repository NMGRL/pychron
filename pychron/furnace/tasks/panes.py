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
from threading import Thread

from enable.component_editor import ComponentEditor
from pyface.tasks.traits_dock_pane import TraitsDockPane
from traits.api import Button, Bool, Str
from traitsui.api import View, Item, UItem, VGroup, HGroup, EnumEditor, spring, \
    ButtonEditor, Tabbed
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pyface.tasks.traits_task_pane import TraitsTaskPane

from pychron.core.ui.lcd_editor import LCDEditor
from pychron.core.ui.led_editor import LEDEditor
from pychron.core.ui.stage_component_editor import VideoComponentEditor
from pychron.envisage.icon_button_editor import icon_button_editor


class ControlPane(TraitsDockPane):
    name = 'Controls'
    id = 'pychron.nmgrlfurnace.controls'

    dump_sample_button = Button('Dump')
    fire_magnets_button = Button('Magnets')
    jitter_button = Button
    jitter_label = Str('Start')
    jittering = Bool
    configure_jitter_button = Button

    refresh_states_button = Button('Refresh')

    funnel_up_button = Button
    funnel_down_button = Button
    feeder_set_home_button = Button('Set Home')
    toggle_advanced_view_button = Button
    _advanced_view_state = Bool(False)

    disable_button = Button

    feeder_slew_positive = Button
    feeder_slew_negative = Button
    feeder_stop_button = Button

    clear_sample_states_button = Button('Clear Dumped Samples')

    def _feeder_slew_positive_fired(self):
        self.model.stage_manager.feeder_slew(1)

    def _feeder_slew_negative_fired(self):
        self.model.stage_manager.feeder_slew(-1)

    def _feeder_stop_button_fired(self):
        self.model.stage_manager.feeder_stop()

    def _feeder_set_home_button_fired(self):
        self.model.stage_manager.feeder.set_home()

    def _disable_button_fired(self):
        self.model.setpoint = 0

    def _funnel_up_button_fired(self):
        def func():
            self.model.raise_funnel()

        t = Thread(target=func)
        t.start()

    def _funnel_down_button_fired(self):
        def func():
            self.model.lower_funnel()

        t = Thread(target=func)
        t.start()

    def _dump_sample_button_fired(self):
        self.model.dump_sample()

    def _fire_magnets_button_fired(self):
        self.model.fire_magnets()

    def _jitter_button_fired(self):
        if not self.jittering:
            self.model.start_jitter_feeder()
            self.jitter_label = 'Stop'
        else:
            self.model.stop_jitter_feeder()
            self.jitter_label = 'Start'
        self.jittering = not self.jittering

    def _configure_jitter_button_fired(self):
        self.model.configure_jitter_feeder()

    def _toggle_advanced_view_button_fired(self):
        self._advanced_view_state = not self._advanced_view_state

    def _refresh_states_button_fired(self):
        self.model.refresh_states()

    def _clear_sample_states_button_fired(self):
        self.model.clear_sample_states()

    def trait_context(self):
        return {'object': self.model,
                'pane': self,
                'tray_manager': self.model.stage_manager.tray_calibration_manager,
                'stage_manager': self.model.stage_manager}

    def traits_view(self):
        # cali_grp = VGroup(UItem('tray_manager.calibrate',
        #                         enabled_when='stage_manager.stage_map_name',
        #                         editor=ButtonEditor(label_value='tray_manager.calibration_step')),
        #                   HGroup(Readonly('tray_manager.x', format_str='%0.3f'),
        #                          Readonly('tray_manager.y', format_str='%0.3f')),
        #                   Readonly('tray_manager.rotation', format_str='%0.3f'),
        #                   Readonly('tray_manager.scale', format_str='%0.4f'),
        #                   Readonly('tray_manager.error', format_str='%0.2f'),
        #                   UItem('tray_manager.calibrator', style='custom', editor=InstanceEditor()),
        #                   CustomLabel('tray_manager.calibration_help',
        #                               color='green',
        #                               height=75, width=300),
        #
        #                   show_border=True, label='Calibration')
        c_grp = VGroup(HGroup(Item('setpoint'),
                              UItem('water_flow_led', editor=LEDEditor(label='H2O Flow')),
                              spring, icon_button_editor('pane.disable_button', 'cancel')),
                       VGroup(UItem('temperature_readback', editor=LCDEditor())),
                       label='Controller', show_border=True)

        feeder_grp = VGroup(HGroup(Item('stage_manager.calibrated_position_entry', label='Hole'),
                                   icon_button_editor('pane.toggle_advanced_view_button', 'cog')),
                            VGroup(Item('stage_manager.feeder.position', label='Position (units)'),
                                   Item('stage_manager.feeder.velocity'),
                                   Item('pane.feeder_set_home_button'),
                                   HGroup(icon_button_editor('pane.feeder_slew_positive', 'arrow_left'),
                                          icon_button_editor('pane.feeder_slew_negative', 'arrow_right'),
                                          icon_button_editor('pane.feeder_stop_button', 'cancel')),
                                   visible_when='pane._advanced_view_state'),
                            show_border=True, label='Position')

        funnel_grp = VGroup(HGroup(icon_button_editor('pane.funnel_up_button', 'arrow_up',
                                                      enabled_when='funnel_up_enabled', tooltip='Raise Funnel'),
                                   icon_button_editor('pane.funnel_down_button', 'arrow_down', tooltip='Lower Funnel',
                                                      enabled_when='funnel_down_enabled')),
                            show_border=True, label='Funnel')
        jitter_grp = HGroup(UItem('pane.jitter_button', editor=ButtonEditor(label_value='pane.jitter_label')),
                            icon_button_editor('pane.configure_jitter_button', 'cog', tooltip='Configure Jitter'),
                            show_border=True, label='Jitter')

        dump_grp = HGroup(UItem('pane.dump_sample_button',
                                tooltip='Complete sample dumping procedure'),
                          UItem('pane.fire_magnets_button',
                                enabled_when='not magnets_firing',
                                tooltip='Execute the magnet sequence'),
                          UItem('pane.clear_sample_states_button'),
                          show_border=True, label='Dump')

        d1 = VGroup(feeder_grp, funnel_grp, jitter_grp, dump_grp)
        d2 = VGroup(
            # UItem('pane.refresh_states_button'),
            UItem('dumper_canvas', editor=ComponentEditor()))
        d_grp = HGroup(d1, d2, label='Dumper', show_border=True)

        v_grp = VGroup(UItem('video_canvas', editor=VideoComponentEditor()),
                       visible_when='video_enabled',
                       label='Camera')

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
                       HGroup(icon_button_editor('snapshot_button', 'camera'),
                              show_border=True, label='Snapshot', ),
                       label='Graph')
        v = View(VGroup(c_grp,
                        HGroup(Tabbed(d_grp, v_grp, g_grp))))
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
