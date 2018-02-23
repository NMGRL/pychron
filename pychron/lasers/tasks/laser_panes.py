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
from __future__ import absolute_import
from enable.component_editor import ComponentEditor
from pyface.tasks.traits_dock_pane import TraitsDockPane
from pyface.tasks.traits_task_pane import TraitsTaskPane
from traits.api import Property
from traitsui.api import View, UItem, Group, InstanceEditor, HGroup, \
    EnumEditor, Item, spring, Spring, ButtonEditor, VGroup, RangeEditor, \
    ListStrEditor, Handler

from pychron.core.ui.custom_label_editor import CustomLabel
from pychron.core.ui.image_editor import ImageEditor
from pychron.core.ui.led_editor import LEDEditor
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.experiment.utilities.identifier import pretty_extract_device


class BaseLaserPane(TraitsTaskPane):
    def trait_context(self):
        return {'object': self.model.stage_manager}

    def traits_view(self):
        editor = self.model.stage_manager.canvas_editor_factory()
        return View(UItem('canvas', style='custom', editor=editor))


class AxesPane(TraitsDockPane):
    name = 'Axes'

    def traits_view(self):
        agrp = UItem('stage_controller', style='custom')
        return View(agrp)


class StageControlPane(TraitsDockPane):
    name = 'Stage'

    def trait_context(self):
        return {'canvas': self.model.stage_manager.canvas,
                'stage_manager': self.model.stage_manager,
                'degasser': self.model.degasser,
                'tray_calibration': self.model.stage_manager.tray_calibration_manager,
                'object': self.model}

    def _get_tabs(self):
        canvas_grp = VGroup(Item('canvas.show_bounds_rect', label='Show Bounds Rectangle'),
                            Item('canvas.show_grids', label='Show Grids'),
                            VGroup(HGroup(Item('canvas.show_laser_position', label='Display Current'),
                                          UItem('canvas.crosshairs_color'),
                                          Item('canvas.crosshairs_line_width', label='Line Wt.')),
                                   Item('canvas.show_hole_label', label='Display Hole Label'),
                                   HGroup(
                                       Item('canvas.show_desired_position',
                                            label='Show Desired'),
                                       UItem('canvas.desired_position_color')),
                                   Item('canvas.crosshairs_kind', label='Kind'),
                                   Item('canvas.crosshairs_radius', label='Radius'),
                                   HGroup(Item('canvas.crosshairs_offsetx', label='Offset (mm)'),
                                          UItem('canvas.crosshairs_offsety')),
                                   Item('canvas.crosshairs_offset_color', label='Offset Color'),
                                   label='Crosshairs',
                                   show_border=True),
                            label='Canvas')

        tabs = Group(UItem('stage_manager.stage_controller', style='custom',
                           label='Axes'),
                     canvas_grp,
                     layout='tabbed')

        if self.model.stage_manager.__class__.__name__ == 'VideoStageManager':
            degasser_grp = VGroup(HGroup(VGroup(UItem('degas_test_button'),
                                         show_border=True, label='Testing'),
                                  VGroup(Item('degasser.threshold'),
                                         show_border=True, label='Preprocess'),
                                         icon_button_editor('degasser.edit_pid_button','cog'),
                                         icon_button_editor('degasser.save_button', 'save'),
                                         VGroup(Item('degasser.pid.kp'),
                                                Item('degasser.pid.ki'),
                                                Item('degasser.pid.kd')),
                                         show_border=True, label='PID'),
                                  UItem('degasser.plot_container', style='custom', editor=ComponentEditor()),
                                  label='Degas', show_border=True)

            mvgrp = VGroup(VGroup(UItem('stage_manager.autocenter_manager.display_image',
                                        width=240, height=240,
                                        editor=ImageEditor(refresh='stage_manager.autocenter_manager.'
                                                                   'display_image.refresh_needed'))),
                           label='Machine Vision', show_border=True)

            recgrp = VGroup(HGroup(icon_button_editor('stage_manager.snapshot_button',
                                                      'camera',
                                                      tooltip='Take a snapshot'),
                                   icon_button_editor('stage_manager.record',
                                                      'media-record',
                                                      tooltip='Record video'),
                                   CustomLabel('stage_manager.record_label',
                                               color='red')),
                            HGroup(Item('stage_manager.auto_save_snapshot', label='Auto Save'),
                                   Item('stage_manager.render_with_markup', label='Add Markup')),
                            show_border=True,
                            label='Recording')

            cfggrp = VGroup(Item('stage_manager.camera_zoom_coefficients',
                                 label='Coeff.'),
                            icon_button_editor('stage_manager.configure_camera_device_button', 'cog',
                                               tooltip='Reload camera configuration file'),
                            show_border=True, label='Zoom')
            # camera_grp.content.extend((HGroup(cfggrp, recgrp), mvgrp))

            camera_grp = VGroup(HGroup(cfggrp, recgrp),
                                mvgrp,
                                visible_when='use_video', label='Camera')
            tabs.content.append(camera_grp)
            tabs.content.append(degasser_grp)

        mode = self.model.mode
        if mode != 'client':
            pp_grp = UItem('stage_manager.points_programmer',
                           label='Points',
                           style='custom')
            tabs.content.append(pp_grp)

            cal_help_grp = VGroup(CustomLabel('tray_calibration.calibration_help',
                                              color='green'),
                                  label='Help', show_border=True)
            cal_results_grp = VGroup(HGroup(Item('tray_calibration.x',
                                                 format_str='%0.3f',
                                                 style='readonly'),
                                            Item('tray_calibration.y',
                                                 format_str='%0.3f',
                                                 style='readonly')),
                                     Item('tray_calibration.rotation',
                                          format_str='%0.3f', style='readonly'),
                                     Item('tray_calibration.scale', format_str='%0.4f',
                                          style='readonly'),
                                     Item('tray_calibration.error', format_str='%0.2f',
                                          style='readonly'),
                                     label='Results', show_border=True)
            holes_grp = VGroup(HGroup(UItem('tray_calibration.add_holes_button',
                                            tooltip='Add Holes'),
                                      UItem('tray_calibration.reset_holes_button',
                                            tooltip='Reset Holes')),
                               UItem('tray_calibration.holes_list',
                                     editor=ListStrEditor()))
            cal_grp = HGroup(UItem('tray_calibration.style',
                                   enabled_when='not tray_calibration.isCalibrating()'),
                             UItem('stage_manager.stage_map_name',
                                   editor=EnumEditor(name='stage_manager.stage_map_names')),
                             UItem('tray_calibration.calibrate',
                                   enabled_when='tray_calibration.calibration_enabled',
                                   editor=ButtonEditor(label_value='tray_calibration.calibration_step'),
                                   width=-125),
                             UItem('tray_calibration.cancel_button',
                                   enabled_when='tray_calibration.isCalibrating()'),
                             UItem('tray_calibration.set_center_button'))
            tc_grp = VGroup(cal_grp,
                            # holes_grp,
                            HGroup(cal_results_grp, cal_help_grp),
                            label='Calibration')

            tabs.content.append(tc_grp)
        return tabs

    def traits_view(self):
        pgrp = HGroup(UItem('stage_manager.calibrated_position_entry',
                            tooltip='Enter a position e.g 1 for a hole, '
                                    'or 3,4 for X,Y'),
                      icon_button_editor('stage_manager.autocenter_button', 'find',
                                         tooltip='Do an autocenter at the current location',
                                         enabled_when='stage_manager.autocenter_manager.use_autocenter'),
                      label='Calibrated Position',
                      show_border=True)
        hgrp = HGroup(UItem('stage_manager.stop_button'),
                      UItem('stage_manager.home'),
                      UItem('stage_manager.home_option',
                            editor=EnumEditor(
                                name='stage_manager.home_options')))
        tabs = self._get_tabs()
        v = View(VGroup(hgrp, pgrp, tabs))
        return v


class ControlPane(TraitsDockPane):
    name = 'Control'

    movable = False
    closable = True
    floatable = False

    def traits_view(self):
        led_grp = HGroup(UItem('enabled',
                               editor=LEDEditor(colors=['red', 'green']),
                               style='custom',
                               height=-35),
                         UItem('enable', editor=ButtonEditor(label_value='enable_label')))

        status_grp = HGroup(spring, CustomLabel('status_text',
                                                weight='bold',
                                                use_color_background=False,
                                                # bgcolor='transparent',
                                                color='orange', size=40),
                            spring)
        request_grp = HGroup(Item('requested_power',
                                  style='readonly',
                                  format_str='%0.2f',
                                  width=100),
                             Spring(springy=False, width=50),
                             UItem('units', style='readonly'),
                             spring)

        v = View(VGroup(led_grp,
                        spring,
                        status_grp,
                        spring,
                        request_grp, show_border=True))
        return v


class SupplementalPane(TraitsDockPane):
    pass


# ===============================================================================
# generic
# ===============================================================================

class PulseHandler(Handler):
    def close(self, info, ok):
        info.object.dump_pulse()
        return ok


class PulsePane(TraitsDockPane):
    id = 'pychron.lasers.pulse'
    name = 'Pulse'

    def trait_context(self):
        ctx = super(PulsePane, self).trait_context()
        ctx['object'] = self.model.pulse
        return ctx

    def traits_view(self):
        agrp = VGroup(HGroup(Item('power', tooltip='Hit Enter for change to take effect'),
                             Item('units', style='readonly', show_label=False),
                             spring,
                             Item('duration', label='Duration (s)', tooltip='Set the laser pulse duration in seconds'),
                             Item('pulse_button',
                                  editor=ButtonEditor(label_value='pulse_label'),
                                  show_label=False,
                                  enabled_when='enabled')))
        mgrp = VGroup(HGroup(Spring(width=-5, springy=False),
                             Item('object.wait_control.high', label='Set Max. Seconds'),
                             spring, UItem('object.wait_control.continue_button')),
                      HGroup(Spring(width=-5, springy=False),
                             Item('object.wait_control.current_time', show_label=False,
                                  editor=RangeEditor(mode='slider',
                                                     low=1,
                                                     # low_name='low_name',
                                                     high_name='object.wait_control.duration')),
                             CustomLabel('object.wait_control.current_time',
                                         size=14,
                                         weight='bold')), show_border=True)

        v = View(VGroup(agrp, mgrp, show_border=True), id='pulse', handler=PulseHandler())
        return v


class OpticsPane(TraitsDockPane):
    id = 'pychron.lasers.optics'
    name = 'Optics'

    def traits_view(self):
        v = View(Group(UItem('laser_controller',
                             editor=InstanceEditor(),
                             style='custom'),
                       show_border=True))
        return v


class ClientMixin(object):
    name = Property(depends_on='model')
    id = 'pychron.lasers.client'

    def _get_name(self):
        n = 'Laser Client'
        if self.model:
            n = pretty_extract_device(self.model.name)
        return n

    def traits_view(self):
        pos_grp = VGroup(UItem('move_enabled_button'),
                         VGroup(HGroup(Item('position'),
                                       UItem(
                                           'object.stage_manager.stage_map_name',
                                           editor=EnumEditor(
                                               name='object.stage_manager.stage_map_names')),
                                       UItem('stage_stop_button')),
                                Item('x',
                                     editor=RangeEditor(low=-25.0, high=25.0)),
                                Item('y',
                                     editor=RangeEditor(low=-25.0, high=25.0)),
                                Item('z',
                                     editor=RangeEditor(low=-25.0, high=25.0)),
                                enabled_when='_move_enabled'),
                         label='Positioning')

        # ogrp = Group(UItem('optics_client', style='custom'),
        #              label='Optics')
        # cgrp = Group(UItem('controls_client', style='custom'),
        #              defined_when='controls_client',
        #              label='Controls')

        tgrp = Group(
            # cgrp,
            # ogrp,
            pos_grp, layout='tabbed')

        egrp = HGroup(UItem('enabled', editor=LEDEditor(colors=['red', 'green'])),
                      UItem('enable',
                            editor=ButtonEditor(label_value='enable_label')),
                      UItem('fire_laser_button', enabled_when='enabled'),
                      Item('output_power', label='Power'),
                      UItem('units'),
                      spring,
                      icon_button_editor('snapshot_button', 'camera'),
                      icon_button_editor('test_connection_button',
                                         'connect', tooltip='Test Connection'))
        v = View(VGroup(egrp, tgrp))
        return v


class ClientPane(TraitsTaskPane, ClientMixin):
    pass
    # def traits_view(self):
    #     v = View(
    #         Item('test_connection_button', show_label=False),
    #         HGroup(
    #             UItem('enabled_led', editor=LEDEditor()),
    #             UItem('enable', editor=ButtonEditor(label_value='enable_label'))),
    #         Item('position'),
    #         UItem('snapshot_button'),
    #         Item('x', editor=RangeEditor(low=-25.0, high=25.0)),
    #         Item('y', editor=RangeEditor(low=-25.0, high=25.0)),
    #         Item('z', editor=RangeEditor(low=-25.0, high=25.0)))
    #     return v


class ClientDockPane(TraitsDockPane, ClientMixin):
    pass


class AuxilaryGraphPane(TraitsDockPane):
    name = 'Auxilary Graph'

    def traits_view(self):
        v = View(UItem('auxilary_graph', editor=ComponentEditor()))
        return v

# ============= EOF =============================================
