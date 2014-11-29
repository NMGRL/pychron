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
from traits.api import Bool, Str, Enum, File, Int, Directory, \
    Color, Range
from traitsui.api import View, Item, VGroup, HGroup, Group
# from apptools.preferences.api import PreferencesHelper
from envisage.ui.tasks.preferences_pane import PreferencesPane
from pychron.envisage.tasks.base_preferences_helper import BasePreferencesHelper

# ============= standard library imports ========================
# ============= local library imports  ==========================
# def qt_color_convert(value):
#    value = value.split('(')[1]
#    value = value[:-1]
#    value = map(float, value.split(','))
#    value = map(lambda x: x * 255, value)
#    return value
# #            PySide.QtGui.QColor.fromRgbF(1.000000, 0.128695, 0.235080, 1.000000)


class LaserPreferences(BasePreferencesHelper):
    pass
#    def _get_value(self, name, value):
#        print name , value
#        if name == 'crosshairs_color':
#            value = value.split('(')[1]
#            value = value[:-1]
#            value = map(float, value.split(','))
#            value = map(lambda x: x * 255, value)
#  #            PySide.QtGui.QColor.fromRgbF(1.000000, 0.128695, 0.235080, 1.000000)
#        else:
#            value = super(LaserPreferences, self)._get_value(name, value)
#        return value

class FusionsLaserPreferences(LaserPreferences):
    use_video = Bool(False)
    video_output_mode = Enum('MPEG', 'Raw')
    ffmpeg_path = File

    video_identifier = Str
    use_video_server = Bool(False)
    video_server_port = Int(1084)
    video_server_quality = Range(1, 75, 75)

    show_grids = Bool(True)
    show_laser_position = Bool(True)
    show_desired_position = Bool(True)
    show_map = Bool(False)

    crosshairs_kind = Enum('BeamRadius', 'UserRadius', 'MaskRadius')
    crosshairs_color = Color('maroon')
    crosshairs_radius = Range(0.0, 4.0, 1.0)

    desired_position_color = Color('green')
    calibration_style = Enum('Tray', 'Free')
    scaling = Range(1.0, 2.0, 1)

    use_autocenter = Bool(False)
    render_with_markup = Bool(False)
    crosshairs_offsetx = Int(0)
    crosshairs_offsety = Int(0)
    crosshairs_offset_color = Color('blue')

    show_patterning = Bool(True)
    video_directory = Directory
    use_video_archiver = Bool(True)
    video_archive_months = Range(0, 12, 1)
    video_archive_hours = Range(0, 23, 0)
    video_archive_days = Range(0, 31, 7)

#     recording_zoom = Range(0, 100.0, 0.0)

    record_patterning = Bool(False)
    record_brightness = Bool(True)
#     record_lasing_video = Bool(False)
#     record_lasing_power = Bool(False)

    use_calibrated_power = Bool(True)
    show_bounds_rect = Bool(True)

    def _get_value(self, name, value):
        if 'color' in name:
            value = value.split('(')[1]
            value = value[:-1]
            value = map(float, value.split(','))
            value = ','.join(map(lambda x: str(int(x * 255)), value))
        else:
            value = super(LaserPreferences, self)._get_value(name, value)
        return value


class FusionsDiodePreferences(FusionsLaserPreferences):
    name = 'Fusions Diode'
    preferences_path = 'pychron.fusions.diode'

class FusionsCO2Preferences(FusionsLaserPreferences):
    name = 'Fusions CO2'
    preferences_path = 'pychron.fusions.co2'

class FusionsUVPreferences(FusionsLaserPreferences):
    name = 'Fusions UV'
    preferences_path = 'pychron.fusions.uv'



# ===============================================================================
# Panes
# ===============================================================================
class FusionsLaserPreferencesPane(PreferencesPane):


    def traits_view(self):
        grps = self.get_additional_groups()
        v = View(Group(*grps, layout='tabbed'))
        return v

    def get_additional_groups(self):
        archivergrp = Group(Item('use_video_archiver'),
                            Item('video_archive_days',
                                  label='Archive after N. days',
                                  enabled_when='use_video_archiver',
                                  ),
                            Item('video_archive_hours',
                                  label='Archive after N. hours',
                                  enabled_when='use_video_archiver',
                                  ),
                             Item('video_archive_months',
                                  label='Delete after N. months',
                                  enabled_when='use_video_archiver',
                                  ),
                             show_border=True,
                             label='Archiver'
                           )
        recgrp = Group(
#                        Item('record_lasing_video', label='Record Lasing'),
#                        Item('record_brightness',
#                             label='Record Brightness Measure',
#                             ),
                       Item('video_directory', label='Save to',
                            enabled_when='record_lasing_video_video'),
#                        Item('recording_zoom', enabled_when='record_lasing_video'),
                       show_border=True,
                       label='Record'
                     )
        vservergrp = VGroup(Item('use_video_server', label='Use Server'),
                                Item('video_server_port', label='Port',
                                     enabled_when='use_video_server'),
                                Item('video_server_quality', label='Quality',
                                     enabled_when='use_video_server'),
                                show_border=True,
                                label='Server'
                                )
        videogrp = VGroup(Item('use_video'),
                        VGroup(
                         Item('video_identifier', label='ID',
                              enabled_when='use_video'),
                         Item('video_output_mode', label='Output Mode'),
                         Item('ffmpeg_path', label='FFmpeg Location'),
                         Item('use_autocenter', label='Auto Center'),
                         Item('render_with_markup', label='Render Snapshot with markup'),
                         recgrp,
                         archivergrp,
                         vservergrp,
                         enabled_when='use_video'
                         ),

                      label='Video')
        canvasgrp = VGroup(
               Item('show_bounds_rect'),
               Item('show_map'),
               Item('show_grids'),
               Item('show_laser_position'),
               Item('show_desired_position'),
               Item('desired_position_color', show_label=False,
                     enabled_when='show_desired_position'),
               Item('crosshairs_kind', label='Crosshairs',
                     enabled_when='show_laser_position'),
               Item('crosshairs_radius',
                    visible_when='crosshairs_kind=="UserRadius"'
                    ),
               Item('crosshairs_color', enabled_when='show_laser_position'),
               HGroup(
                      Item('crosshairs_offsetx', label='Offset'),
                      Item('crosshairs_offsety', show_label=False),
                      ),
               Item('crosshairs_offset_color', show_label=False,
                    ),
               Item('calibration_style'),
               Item('scaling'),
               label='Canvas',
               )

        patgrp = Group(Item('record_patterning'),
                       Item('show_patterning'), label='Pattern')
        powergrp = Group(
#                         Item('record_lasing_power'),
                        Item('use_calibrated_power'),
                         label='Power')
        return [canvasgrp, videogrp,
                 patgrp, powergrp
                 ]

class FusionsDiodePreferencesPane(FusionsLaserPreferencesPane):
    category = 'Fusions Diode'
    model_factory = FusionsDiodePreferences

class FusionsCO2PreferencesPane(FusionsLaserPreferencesPane):
    category = 'Fusions CO2'
    model_factory = FusionsCO2Preferences

class FusionsUVPreferencesPane(FusionsLaserPreferencesPane):
    category = 'Fusions UV'
    model_factory = FusionsUVPreferences

# ============= EOF =============================================
