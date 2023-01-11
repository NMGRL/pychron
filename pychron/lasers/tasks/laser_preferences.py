# ===============================================================================
# Copyright 2013 Jake Ross
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
from __future__ import absolute_import

from envisage.ui.tasks.preferences_pane import PreferencesPane
from traits.api import Bool, Enum, Directory, Color, Range, Float, Int
from traitsui.api import View, Item, VGroup, HGroup, Group, UItem

from pychron.core.pychron_traits import BorderVGroup
from pychron.envisage.tasks.base_preferences_helper import BasePreferencesHelper
from pychron.pychron_constants import (
    SIZES,
    FUSIONS_DIODE,
    FUSIONS_CO2,
    FUSIONS_UV,
    OSTECH_DIODE,
    TAP_DIODE,
)


class LaserPreferences(BasePreferencesHelper):
    use_video = Bool(False)
    # video_output_mode = Enum('MPEG', 'Raw')
    # ffmpeg_path = File
    # video_identifier = Str

    use_media_storage = Bool
    keep_local_copy = Bool
    auto_upload = Bool
    burst_delay = Int(250)
    # use_video_server = Bool(False)
    # video_server_port = Int(1084)
    # video_server_quality = Range(1, 75, 75)

    show_grids = Bool(True)
    show_laser_position = Bool(True)
    show_desired_position = Bool(True)
    show_map = Bool(False)

    crosshairs_kind = Enum("BeamRadius", "UserRadius", "MaskRadius")
    crosshairs_color = Color("maroon")
    crosshairs_radius = Range(0.0, 10.0, 1.0)

    desired_position_color = Color("green")
    calibration_style = Enum("Tray", "Free")
    scaling = Range(1.0, 2.0, 1)

    use_autocenter = Bool(False)
    autocenter_blur = Int
    autocenter_stretch_intensity = Bool(False)
    autocenter_use_adaptive_threshold = Bool(False)
    autocenter_blocksize = Int
    autocenter_blocksize_step = Int
    autocenter_search_step = Int
    autocenter_search_n = Int
    autocenter_search_width = Int
    dimension_multiplier = Float(1)

    render_with_markup = Bool(False)
    crosshairs_offsetx = Float(0)
    crosshairs_offsety = Float(0)
    crosshairs_offset_color = Color("blue")
    crosshairs_line_width = Float(1.0)

    aux_crosshairs_kind = Enum("BeamRadius", "UserRadius", "MaskRadius")
    aux_crosshairs_radius = Range(0.0, 10.0, 1.0)
    aux_crosshairs_offsetx = Float(0)
    aux_crosshairs_offsety = Float(0)
    aux_crosshairs_offset_color = Color("red")
    aux_crosshairs_color = Color("red")
    aux_crosshairs_line_width = Float(1.0)

    show_hole_label = Bool
    hole_label_color = Color
    hole_label_size = Enum(*SIZES)

    show_patterning = Bool(True)
    video_directory = Directory
    use_video_archiver = Bool(True)
    video_archive_months = Range(0, 12, 1)
    video_archive_hours = Range(0, 23, 0)
    video_archive_days = Range(0, 31, 7)

    record_patterning = Bool(False)
    record_brightness = Bool(True)

    use_calibrated_power = Bool(True)
    show_bounds_rect = Bool(True)


class FusionsLaserPreferences(LaserPreferences):
    pass
    # def _get_value(self, name, value):
    #     if 'color' in name:
    #         value = value.split('(')[1]
    #         value = value[:-1]
    #         value = map(float, value.split(','))
    #         value = ','.join(map(lambda x: str(int(x * 255)), value))
    #     else:
    #         value = super(LaserPreferences, self)._get_value(name, value)
    #     return value


class FusionsDiodePreferences(FusionsLaserPreferences):
    name = FUSIONS_DIODE
    preferences_path = "pychron.fusions.diode"


class FusionsCO2Preferences(FusionsLaserPreferences):
    name = FUSIONS_CO2
    preferences_path = "pychron.fusions.co2"


class FusionsUVPreferences(FusionsLaserPreferences):
    name = "Fusions UV"
    preferences_path = "pychron.fusions.uv"


class OsTechDiodePreferences(LaserPreferences):
    name = OSTECH_DIODE
    preferences_path = "pychron.ostech.diode"


class TAPDiodePreferences(LaserPreferences):
    name = TAP_DIODE
    preferences_path = "pychron.tap.diode"


# ===============================================================================
# Panes
# ===============================================================================
class LaserPreferencesPane(PreferencesPane):
    def traits_view(self):
        grps = self.get_additional_groups()
        v = View(Group(*grps, layout="tabbed"))
        return v

    def get_additional_groups(self):
        archivergrp = Group(
            Item("use_video_archiver"),
            Item(
                "video_archive_days",
                label="Archive after N. days",
                enabled_when="use_video_archiver",
            ),
            Item(
                "video_archive_hours",
                label="Archive after N. hours",
                enabled_when="use_video_archiver",
            ),
            Item(
                "video_archive_months",
                label="Delete after N. months",
                enabled_when="use_video_archiver",
            ),
            show_border=True,
            label="Archiver",
        )

        recgrp = Group(
            Item(
                "video_directory",
                label="Save to",
                enabled_when="record_lasing_video_video",
            ),
            show_border=True,
            label="Record",
        )

        media_storage_grp = VGroup(
            Item("use_media_storage"), Item("keep_local_copy"), Item("auto_upload")
        )

        autocenter_grp = VGroup(
            Item("use_autocenter", label="Auto Center Enabled"),
            VGroup(
                VGroup(
                    Item("autocenter_blur", label="Blur"),
                    Item("autocenter_stretch_intensity", label="Stretch Intensity"),
                    Item("dimension_multiplier", label="Dimension Multiplier"),
                    show_border=True,
                    label="Preprocess",
                ),
                VGroup(
                    Item("autocenter_search_step", label="Step"),
                    Item("autocenter_search_n", label="N"),
                    Item("autocenter_search_width", label="Width"),
                    Item(
                        "autocenter_use_adaptive_threshold",
                        label="Use Adaptive Threshold",
                    ),
                    Item(
                        "autocenter_blocksize",
                        label="Block Size",
                        enabled_when="autocenter_use_adaptive_threshold",
                    ),
                    Item(
                        "autocenter_blocksize_step",
                        label="Block Size Step",
                        enabled_when="autocenter_use_adaptive_threshold",
                    ),
                    show_border=True,
                    label="Search",
                ),
                show_border=True,
            ),
            enabled_when="use_video",
            label="Autocenter",
        )

        videogrp = VGroup(
            Item("use_video"),
            VGroup(
                # Item('video_identifier', label='ID',
                #      enabled_when='use_video'),
                # Item('video_output_mode', label='Output Mode'),
                # Item('ffmpeg_path', label='FFmpeg Location'),
                Item("render_with_markup", label="Render Snapshot with markup"),
                Item(
                    "burst_delay",
                    label="Burst Delay (ms)",
                    tooltip="delay between snapshots in burst mode",
                ),
                recgrp,
                archivergrp,
                media_storage_grp,
                enabled_when="use_video",
            ),
            label="Video",
        )

        crosshairs_grp = BorderVGroup(
            HGroup(
                Item("show_laser_position", label="Display Current Position"),
                Item(
                    "crosshairs_kind",
                    label="Crosshairs",
                    enabled_when="show_laser_position",
                ),
            ),
            Item("crosshairs_radius", visible_when='crosshairs_kind=="UserRadius"'),
            Item("crosshairs_color", enabled_when="show_laser_position"),
            Item("crosshairs_line_width", enabled_when="show_laser_position"),
            HGroup(
                Item("crosshairs_offsetx", label="Offset"), UItem("crosshairs_offsety")
            ),
            UItem("crosshairs_offset_color"),
            label="Crosshairs",
        )
        aux_crosshairs_grp = BorderVGroup(
            HGroup(
                Item(
                    "aux_crosshairs_kind",
                    label="Crosshairs",
                    enabled_when="aux_show_laser_position",
                )
            ),
            Item(
                "aux_crosshairs_radius",
                visible_when='aux_crosshairs_kind=="UserRadius"',
            ),
            Item("aux_crosshairs_color", enabled_when="aux_show_laser_position"),
            Item("aux_crosshairs_line_width", enabled_when="aux_show_laser_position"),
            HGroup(
                Item("aux_crosshairs_offsetx", label="Offset"),
                UItem("aux_crosshairs_offsety"),
            ),
            UItem("aux_crosshairs_offset_color"),
            label="Aux. Crosshairs",
        )

        canvasgrp = VGroup(
            Item("show_bounds_rect", label="Display Bounds Rectangle"),
            Item("show_map", label="Display Map"),
            Item("show_grids", label="Display Grids"),
            Item("show_desired_position", label="Display Desired Position"),
            Item("show_hole_label", label="Display Hole Label"),
            Item("hole_label_color"),
            Item("hole_label_size"),
            UItem("desired_position_color", enabled_when="show_desired_position"),
            crosshairs_grp,
            aux_crosshairs_grp,
            Item("scaling"),
            label="Canvas",
        )

        patgrp = Group(
            Item("record_patterning"), Item("show_patterning"), label="Pattern"
        )
        powergrp = Group(Item("use_calibrated_power"), label="Power")
        return [canvasgrp, videogrp, autocenter_grp, patgrp, powergrp]


class FusionsLaserPreferencesPane(LaserPreferencesPane):
    pass


class FusionsDiodePreferencesPane(FusionsLaserPreferencesPane):
    category = FUSIONS_DIODE
    model_factory = FusionsDiodePreferences


class FusionsCO2PreferencesPane(FusionsLaserPreferencesPane):
    category = FUSIONS_CO2
    model_factory = FusionsCO2Preferences


class FusionsUVPreferencesPane(FusionsLaserPreferencesPane):
    category = FUSIONS_UV
    model_factory = FusionsUVPreferences


class OsTechDiodePreferencesPane(LaserPreferencesPane):
    category = OSTECH_DIODE
    model_factory = OsTechDiodePreferences


class TAPDiodePreferencesPane(LaserPreferencesPane):
    category = TAP_DIODE
    model_factory = TAPDiodePreferences


# ============= EOF =============================================
