# ===============================================================================
# Copyright 2016 Jake Ross
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
from traits.api import Property, Instance
from traitsui.api import View, Item, Controller, VGroup, HGroup, UItem, EnumEditor, TabularEditor
from traitsui.menu import Action
from traitsui.tabular_adapter import TabularAdapter

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.ui.text_editor import myTextEditor
from pychron.entry.dvc_import import DVCImporterModel
from pychron.envisage.icon_button_editor import icon_button_editor


class ImportNameAdapter(TabularAdapter):
    columns = [('Name', 'name')]


class ImportedNameAdapter(TabularAdapter):
    columns = [('Name', 'name'), ('Skipped', 'skipped')]
    skipped_text = Property

    def _get_skipped_text(self):
        return 'Yes' if self.item.skipped else ''

    def get_bg_color(self, obj, trait, row, column=0):
        color = 'white'
        if self.item.skipped:
            color = 'red'
        return color


class ImportButton(Action):
    name = 'Import'
    action = 'do_import'


class DVCImporterView(Controller):
    model = Instance(DVCImporterModel)

    def do_import(self, info):
        self.model.do_import()

    def traits_view(self):
        s_grp = HGroup(UItem('source', editor=EnumEditor(name='sources')),
                       UItem('filter_str', editor=myTextEditor(multiline=False,
                                                               placeholder='Filter Irradiations')),
                       icon_button_editor('clear_filter_button', 'clear'))

        a_grp = HGroup(Item('available_irradiations', show_label=False,
                            editor=TabularEditor(adapter=ImportNameAdapter(),
                                                 editable=False,
                                                 selected='selected',
                                                 multi_select=True,
                                                 scroll_to_row='scroll_to_row')),
                       Item('imported_irradiations', show_label=False,
                            editor=TabularEditor(adapter=ImportedNameAdapter(),
                                                 editable=False)))
        v = View(VGroup(s_grp, a_grp),
                 kind='livemodal',
                 resizable=True,
                 width=600,
                 buttons=[ImportButton(), 'OK', 'Cancel'],
                 title='Import Irradiations')
        # v = View(VGroup(
        #                 VGroup(HGroup(spring, Item('data_source')),
        #                        VGroup(source_grp,
        #                               VGroup(HGroup(Item('import_kind', show_label=False),
        #                                             UItem('open_button', visible_when='import_kind=="rid_list"')),
        #                                      UItem('text_selected'),
        #                                      ,
        #                                      label='Results')))),
        #          kind='livemodal',
        #          buttons=['OK', 'Cancel'],
        #          title='Import Irradiations')
        return v

# ============= EOF =============================================
