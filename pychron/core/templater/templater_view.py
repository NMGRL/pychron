# ===============================================================================
# Copyright 2014 Jake Ross
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
from traits.api import Int, Str
from traitsui.api import (
    Item,
    VGroup,
    HGroup,
    ListStrEditor,
    EnumEditor,
    UItem,
    Controller,
)

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.core.pychron_traits import BorderHGroup
from pychron.envisage.icon_button_editor import icon_button_editor


class BaseTemplateView(Controller):
    width = Int(500)
    view_title = Str

    # views
    def _get_main_view(self):
        return VGroup(
            HGroup(
                Item("predefined_label", editor=EnumEditor(name="predefined_labels"))
            ),
            UItem(
                "attributes",
                editor=ListStrEditor(editable=False, activated="activated"),
            ),
            BorderHGroup(
                UItem("label"),
                icon_button_editor(
                    "clear_button", "clear", tooltip="Clear current label"
                ),
                icon_button_editor(
                    "add_label_button",
                    "add",
                    enabled_when="add_enabled",
                    tooltip="Save current label to the predefined list",
                ),
                icon_button_editor(
                    "delete_label_button",
                    "delete",
                    enabled_when="delete_enabled",
                    tooltip="Remove current label from the predefined list",
                ),
                label="Label",
            ),
            BorderHGroup(UItem("example", style="readonly"), label="Example"),
        )

    def _get_additional_groups(self):
        pass

    def traits_view(self):
        vg = VGroup(self._get_main_view())
        grps = self._get_additional_groups()
        if grps:
            vg.content.extend(grps)

        v = okcancel_view(vg, width=self.width, title=self.view_title)
        return v


# ============= EOF =============================================
