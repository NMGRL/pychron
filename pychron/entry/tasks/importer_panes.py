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
from pyface.tasks.traits_dock_pane import TraitsDockPane
from traits.api import Property
from traitsui.api import View, Item, UItem, HGroup, spring, VGroup, TabularEditor

# ============= standard library imports ========================
# ============= local library imports  ==========================
# from traitsui.tabular_adapter import TabularAdapter
#
#
# class ImportNameAdapter(TabularAdapter):
#     columns = [('Name', 'name')]
#
#
# class ImportedNameAdapter(TabularAdapter):
#     columns = [('Name', 'name'), ('Skipped', 'skipped')]
#     skipped_text = Property
#
#     def _get_skipped_text(self):
#         return 'Yes' if self.item.skipped else ''
#
#     def get_bg_color(self, obj, trait, row, column=0):
#         color = 'white'
#         if self.item.skipped:
#             color = 'red'
#         return color


# class ImporterPane(TraitsDockPane):
#     name = 'Importer'
#     id = 'pychron.labnumber.extractor'
#
#     def traits_view(self):
#         v = View(
#             VGroup(
#                 HGroup(
#                     HGroup(Item('include_analyses', label='Analyses'),
#                            Item('include_blanks', label='Blanks'),
#                            Item('include_airs', label='Airs'),
#                            Item('include_cocktails', label='Cocktails'),
#                            label='Include',
#                            show_border=True,
#                     ),
#                     VGroup(
#                         HGroup(spring,
#                                UItem('import_button'),
#                                #Item('dry_run')
#                         ),
#                         label='Import',
#                         show_border=True
#                     )
#                 ),
#                 VGroup(
#                     HGroup(spring, Item('data_source')),
#                     #                         VFold(
#                     VGroup(
#                         VGroup(
#                             Item('object.extractor.dbconn_spec', style='custom', show_label=False),
#                             HGroup(spring, Item('object.extractor.connect_button', show_label=False)),
#                             label='Source'
#                         ),
#                         VGroup(
#
#                             HGroup(Item('import_kind', show_label=False),
#                                    UItem('open_button', visible_when='import_kind=="rid_list"'),
#                             ),
#                             UItem('text_selected'),
#                             HGroup(
#                                 Item('names', show_label=False, editor=TabularEditor(adapter=ImportNameAdapter(),
#                                                                                      editable=False,
#                                                                                      selected='selected',
#                                                                                      multi_select=True,
#                                                                                      scroll_to_row='scroll_to_row'
#                                 )),
#                                 #                                    CustomLabel('custom_label1',
#                                 #                                             color='blue',
#                                 #                                             size=10),
#                                 Item('imported_names', show_label=False,
#                                      editor=TabularEditor(adapter=ImportedNameAdapter(),
#                                                           editable=False,
#                                      ))
#                             ),
#                             #                                    HGroup(spring, Item('import_button', show_label=False)),
#                             label='Results'
#                         )
#                     )
#                 )
#             )
#         )
#         return v

        # ============= EOF =============================================

