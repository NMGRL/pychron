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
from traits.api import Int, Property
from traitsui.api import View, Item, UItem, VGroup, HGroup, EnumEditor, TableEditor, spring, VSplit
# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.extras.checkbox_column import CheckboxColumn
from traitsui.table_column import ObjectColumn
from traitsui.tabular_adapter import TabularAdapter
from pychron.core.ui.combobox_editor import ComboboxEditor
from pychron.core.ui.custom_label_editor import CustomLabel
from pychron.core.ui.tabular_editor import myTabularEditor
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.processing.tasks.browser.pane_model_view import PaneModelView


class ResultsAdapter(TabularAdapter):
    columns = [('Identifier', 'labnumber'),
               ('Aliquot', 'aliquot'),
               ('Analysis Time', 'rundate'),
               ('Irradiation', 'irradiation_info'),
               ('Spec.', 'mass_spectrometer'),
               ('Type', 'analysis_type')]
    font = '10'
    labnumber_width = Int(60)
    mass_spectrometer_width = Int(50)
    aliquot_width = Int(50)
    irradiation_info_width = Int(80)
    rundate_width = Int(120)
    analysis_type_width = Int(90)
    aliquot_text = Property

    def _get_aliquot_text(self):
        return '{:02d}{}'.format(self.item.aliquot, self.item.step)


def selector_name(name):
    return 'object.selector.{}'.format(name)


class BrowserQueryView(PaneModelView):
    def _results_group(self):
        grp = VGroup(
            CustomLabel(selector_name('id_string'), color='maroon'),
            HGroup(
                CustomLabel(selector_name('num_records')), spring,
                Item(selector_name('limit'))),
            Item(selector_name('records'),
                 style='custom',
                 editor=myTabularEditor(adapter=ResultsAdapter(),
                                        selected=selector_name('selected'),
                                        scroll_to_row=selector_name('scroll_to_row'),
                                        column_clicked=selector_name('column_clicked'),
                                        multi_select=True,
                                        operations=['move'],
                                        editable=True,
                                        stretch_last_section=False,
                                        drag_external=True,
                                        dclicked=selector_name('dclicked'),
                                        key_pressed=selector_name('key_pressed')),
                 show_label=False))
        return grp

    def _query_edit_view(self):
        v = View(HGroup(
            UItem('parameter',
                  editor=EnumEditor(name='parameters')),
            UItem('comparator',
                  editor=EnumEditor(name='comparisons')),
            UItem('criterion', editor=ComboboxEditor(name='criteria')),
            # UItem('criterion',
            #       width=-25,
            #       editor=EnumEditor(name='criteria')),
            UItem('chain_rule')),
            height=125)
        return v

    def _table_editor(self):
        cols = [
            CheckboxColumn(name='use', label='',
                           width=30),
            ObjectColumn(name='parameter',
                         editor=EnumEditor(name='parameters'),
                         label='Param.',
                         width=125),
            ObjectColumn(name='comparator',
                         editor=EnumEditor(name='comparisons'),
                         label='',
                         width=50),
            ObjectColumn(name='criterion',
                         editor=EnumEditor(name='criteria'),
                         label='Value',
                         width=125),
            ObjectColumn(name='chain_rule',
                         label='Chain Rule')]

        editor = TableEditor(columns=cols,
                             deletable=True,
                             show_toolbar=True,
                             sortable=False,
                             selected=selector_name('selected_query'),
                             edit_view=self._query_edit_view(),
                             row_factory=self.model.database_selector.query_factory)

        return editor

    def _query_group(self):
        editor = self._table_editor()
        query_itm = Item(selector_name('queries'), show_label=False,
                         style='custom',
                         editor=editor,
                         visible_when='kind=="Database"',
                         height=-200)
        button_grp = HGroup(icon_button_editor(selector_name('add_query_button'),
                                               'add',
                                               tooltip='Add query',
                                               visible_when='kind=="Database"'),
                            icon_button_editor(selector_name('delete_query_button'),
                                               'delete',
                                               tooltip='Delete query',
                                               visible_when='kind=="Database"'),
                            UItem(selector_name('load_recent_button')),
                            Item(selector_name('recent_days')), spring)
        return VGroup(button_grp, query_itm)

    def _filter_grp(self):
        filter_grp = HGroup(
            icon_button_editor(selector_name('search'), 'find'),
            UItem(selector_name('mass_spectrometer'),
                  label='Spec.',
                  editor=EnumEditor(name=selector_name('mass_spectrometers'))),
            UItem(selector_name('analysis_type'),
                  editor=EnumEditor(name=selector_name('analysis_types'))),
            visible_when='kind=="Database"')
        return VGroup(filter_grp)

    def traits_view(self):
        # results_grp = VSplit(self._results_group(),
        #                      VGroup(self._query_group(), filter_grp))
        grp = VSplit(self._results_group(),
                     VGroup(self._query_group(),
                            self._filter_grp()))
        # button_grp = HGroup(icon_button_editor('append_button', 'add',
        #                                        visible_when='append_enabled', tooltip='Append'),
        #                     icon_button_editor('replace_button', 'arrow_refresh',
        #                                        visible_when='replace_enabled', tooltip='Replace'))
        # v = View(VGroup(button_grp, results_grp))
        # v = View(VGroup(results_grp))
        v = View(grp)
        return v

# ============= EOF =============================================



