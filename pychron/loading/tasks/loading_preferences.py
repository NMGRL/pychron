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
from envisage.ui.tasks.preferences_pane import PreferencesPane
from traits.api import Directory
from traitsui.api import View, Item, UItem, HGroup, VGroup

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.pychron_traits import BorderVGroup
from pychron.envisage.tasks.base_preferences_helper import BasePreferencesHelper
from pychron.lasers.tasks.laser_preferences import LaserPreferences


class LoadingPreferences(LaserPreferences):
    name = "Loading"
    preferences_path = "pychron.loading"
    save_directory = Directory


class LoadingPreferencesPane(PreferencesPane):
    model_factory = LoadingPreferences
    category = "Loading"

    def traits_view(self):
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
                Item("aux_crosshairs_enabled", label="Show Aux Crosshairs"),
                Item(
                    "aux_crosshairs_kind",
                    label="Crosshairs",
                    enabled_when="aux_show_laser_position",
                ),
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
        v = View(VGroup(Item("save_directory", label="Output Directory"), canvasgrp))
        return v


# ============= EOF =============================================
