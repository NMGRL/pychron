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
from envisage.ui.tasks.preferences_pane import PreferencesPane
from traits.api import Str
from traitsui.api import View, FileEditor, VGroup, Item

# ============= standard library imports ========================
import os

# ============= local library imports  ==========================
from pychron.paths import paths
from pychron.envisage.tasks.base_preferences_helper import BasePreferencesHelper


class RestonFurnacePreferences(BasePreferencesHelper):
    preferences_path = "pychron.furnace.reston"


class RestonFurnacePreferencesPane(PreferencesPane):
    category = "Reston Furnace"
    model_factory = RestonFurnacePreferences

    def traits_view(self):
        v = View()
        return v


class RestonFurnaceControlPreferences(BasePreferencesHelper):
    preferences_path = "pychron.furnace.reston.control"

    canvas_path = Str
    canvas_config_path = Str
    valves_path = Str


class RestonFurnaceControlPreferencesPane(PreferencesPane):
    category = "Reston Furnace"
    model_factory = RestonFurnaceControlPreferences

    def traits_view(self):
        p_grp = VGroup(
            Item(
                "canvas_path",
                label="Canvas Path",
                editor=FileEditor(
                    root_path=os.path.join(paths.canvas2D_dir, "canvas.xml")
                ),
            ),
            Item("canvas_config_path", label="Config Path", editor=FileEditor()),
            Item(
                "valves_path",
                label="Valves Path",
                editor=FileEditor(
                    root_path=os.path.join(paths.extraction_line_dir, "valves.xml")
                ),
            ),
            show_border=True,
            label="Paths",
        )
        v = View(p_grp)
        return v


# ============= EOF =============================================
