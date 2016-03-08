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
from pyface.timer.do_later import do_after
from traits.api import Button, Bool, Str
from traitsui.api import View, Item, Readonly, UItem, VGroup, HGroup, EnumEditor, spring, \
    InstanceEditor, ButtonEditor, Tabbed
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pyface.tasks.traits_task_pane import TraitsTaskPane
from traitsui.editors import RangeEditor

from pychron.core.ui.custom_label_editor import CustomLabel
from pychron.core.ui.lcd_editor import LCDEditor
from pychron.core.ui.stage_component_editor import VideoComponentEditor
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.core.ui.button_editor import ButtonEditor as mButtonEditor
from pychron.envisage.resources import icon


class ControlPane(TraitsDockPane):
    name = 'Controls'
    id = 'pychron.nmgrlfurnace.controls'

    dump_sample_button = Button('Dump')
    fire_magnets_button = Button('Magnets')
    jitter_button = Button
    jitter_label = Str('Start')
    jittering = Bool
    configure_jitter_button = Button

    funnel_up_button = Button
    funnel_down_button = Button
    funnel_down_enabled = Bool(True)
    funnel_up_enabled = Bool(False)

    toggle_advanced_view_button = Button
    _advanced_view_state = Bool(False)

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
        def func():
            self.funnel_up_enabled = False
            if self.model.raise_funnel():
                self.funnel_down_enabled = True

        t = Thread(target=func)
        t.start()

    def _funnel_down_button_fired(self):
        def func():
            self.funnel_down_enabled = False
            if self.model.lower_funnel():
                self.funnel_up_enabled = True

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
        c_grp = VGroup(HGroup(Item('setpoint'), spring),
                       VGroup(UItem('setpoint_readback', editor=LCDEditor())),
                       label='Controller', show_border=True)

        feeder_grp = VGroup(HGroup(Item('stage_manager.calibrated_position_entry', label='Hole'),
                                   icon_button_editor('pane.toggle_advanced_view_button', 'cog')),
                            VGroup(Item('stage_manager.feeder.position', label='Position (units)'),
                                   Item('stage_manager.feeder.velocity'),
                                   visible_when='pane._advanced_view_state'),
                            show_border=True, label='Position')

        funnel_grp = VGroup(HGroup(icon_button_editor('pane.funnel_up_button', 'arrow_up',
                                                      enabled_when='pane.funnel_up_enabled', tooltip='Raise Funnel'),
                                   icon_button_editor('pane.funnel_down_button', 'arrow_down', tooltip='Lower Funnel',
                                                      enabled_when='pane.funnel_down_enabled')),
                            show_border=True, label='Funnel')
        jitter_grp = HGroup(UItem('pane.jitter_button', editor=ButtonEditor(label_value='pane.jitter_label')),
                            icon_button_editor('pane.configure_jitter_button', 'cog', tooltip='Configure Jitter'),
                            show_border=True, label='Jitter')

        dump_grp = HGroup(UItem('pane.dump_sample_button',
                                tooltip='Complete sample dumping procedure'),
                          UItem('pane.fire_magnets_button', tooltip='Execute the magnet sequence'),
                          show_border=True, label='Dump')

        d1 = VGroup(feeder_grp, funnel_grp, jitter_grp, dump_grp)
        d2 = VGroup(UItem('dumper_canvas', editor=ComponentEditor()))
        d_grp = HGroup(d1, d2, label='Dumper', show_border=True)

        v_grp = VGroup(UItem('video_canvas', editor=VideoComponentEditor()), label='Camera')

        v = View(VGroup(c_grp,
                        HGroup(Tabbed(d_grp, cali_grp, v_grp))))
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
