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
from traits.api import Property, Instance
from traitsui.api import View, Item, Controller, VGroup, HGroup, spring, UItem
from traitsui.editors import TabularEditor
from traitsui.tabular_adapter import TabularAdapter

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.entry.tasks.importer import ImporterModel


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


class ImporterView(Controller):
    model = Instance(ImporterModel)

    def traits_view(self):
        include_grp = HGroup(Item('include_analyses', label='Analyses'),
                             Item('include_blanks', label='Blanks'),
                             Item('include_airs', label='Airs'),
                             Item('include_cocktails', label='Cocktails'),
                             label='Include',
                             show_border=True)
        import_grp = VGroup(HGroup(spring,
                                   UItem('import_button')),
                            label='Import',
                            show_border=True)
        source_grp = VGroup(Item('object.extractor.dbconn_spec', style='custom', show_label=False),
                            HGroup(spring, Item('object.extractor.connect_button', show_label=False)),
                            label='Source')

        v = View(VGroup(HGroup(include_grp, import_grp),
                        VGroup(HGroup(spring, Item('data_source')),
                               VGroup(source_grp,
                                      VGroup(HGroup(Item('import_kind', show_label=False),
                                                    UItem('open_button', visible_when='import_kind=="rid_list"')),
                                             UItem('text_selected'),
                                             HGroup(Item('names', show_label=False,
                                                         editor=TabularEditor(adapter=ImportNameAdapter(),
                                                                              editable=False,
                                                                              selected='selected',
                                                                              multi_select=True,
                                                                              scroll_to_row='scroll_to_row')),
                                                    Item('imported_names', show_label=False,
                                                         editor=TabularEditor(adapter=ImportedNameAdapter(),
                                                                              editable=False))),
                                             label='Results')))),
                 kind='livemodal',
                 buttons=['OK', 'Cancel'],
                 title='Import Irradiations')
        return v

# ============= EOF =============================================



