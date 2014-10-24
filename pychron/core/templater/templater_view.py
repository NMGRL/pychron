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
from traitsui.api import View, Item, VGroup, HGroup, ListStrEditor, EnumEditor, UItem, Controller
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.envisage.tasks.pane_helpers import icon_button_editor


class BaseTemplateView(Controller):
    #views
    def _get_main_view(self):
        return VGroup(HGroup(Item('predefined_label',
                                  editor=EnumEditor(name='predefined_labels'))),
                      UItem('attributes',
                            editor=ListStrEditor(
                                editable=False,
                                activated='activated')),
                      HGroup(UItem('label'),
                             icon_button_editor('clear_button', 'clear',
                                                tooltip='Clear current label'),
                             icon_button_editor('add_label_button', 'add',
                                                enabled_when='add_enabled',
                                                tooltip='Save current label to the predefined list'),
                             icon_button_editor('delete_label_button', 'delete',
                                                enabled_when='delete_enabled',
                                                tooltip='Remove current label from the predefined list'),
                             label='Label',
                             show_border=True),
                      HGroup(UItem('example', style='readonly'), label='Example',
                             show_border=True))

    def _get_additional_groups(self):
        pass

    def traits_view(self):
        vg = VGroup(self._get_main_view())
        grps = self._get_additional_groups()
        if grps:
            vg.content.extend(grps)

        v = View(
            vg,
            resizable=True,
            width=self.width,
            title=self.view_title,
            buttons=['OK', 'Cancel'],
            kind='livemodal')
        return v

#============= EOF =============================================



