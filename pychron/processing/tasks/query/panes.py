#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
from pyface.image_resource import ImageResource
from pyface.tasks.traits_task_pane import TraitsTaskPane
from traits.api import Int, Property
from traitsui.api import View, Item, EnumEditor, TableEditor, VGroup, spring, HGroup,\
    UItem, VSplit, ButtonEditor

#============= standard library imports ========================
#============= local library imports  ==========================
from traitsui.extras.checkbox_column import CheckboxColumn
from traitsui.table_column import ObjectColumn
from traitsui.tabular_adapter import TabularAdapter
from pychron.envisage.tasks.pane_helpers import icon_button_editor
from pychron.paths import paths
from pychron.ui.custom_label_editor import CustomLabel
from pychron.ui.tabular_editor import myTabularEditor


class ResultsAdapter(TabularAdapter):
    columns = [
        #               ('ID', 'rid'),
        ('Lab. #', 'labnumber'),
        ('Aliquot', 'aliquot'),
        ('Analysis Time', 'rundate'),
        #               ('Time', 'runtime'),
        ('Irradiation', 'irradiation_info'),
        ('Spec.', 'mass_spectrometer'),
        ('Type', 'analysis_type')
        #               ('Irradiation', 'irradiation_level')
    ]
    font = 'monospace 12'
    #    rid_width = Int(50)
    labnumber_width = Int(50)
    mass_spectrometer_width = Int(50)
    aliquot_width = Int(50)
    timestamp_width = Int(110)
    irradiation_info_width = Int(65)

    aliquot_text = Property

    def _get_aliquot_text(self):
        return '{:02n}{}'.format(self.item.aliquot, self.item.step)


def selector_name(name):
    return 'object.selector.{}'.format(name)

class AdvancedQueryPane(TraitsTaskPane):
    id = 'pychron.search.query'
    name = 'Advanced Query'

    def _results_group(self):
        grp = VGroup(
            CustomLabel(selector_name('id_string'), color='red'),
            HGroup(
                CustomLabel(selector_name('num_records')), spring,
                Item(selector_name('limit'))),
            Item(selector_name('records'),
                 style='custom',
                 editor=myTabularEditor(adapter=ResultsAdapter(),
                                        selected=selector_name('selected'),
                                        scroll_to_row=selector_name('scroll_to_row'),
                                        #                                                            update='update',
                                        column_clicked=selector_name('column_clicked'),
                                        multi_select=True,
                                        operations=['move'],
                                        editable=True,
                                        drag_external=True,
                                        dclicked=selector_name('dclicked'),
                                        key_pressed=selector_name('key_pressed')
                 ),
                 show_label=False,
                 #                                     height=0.75
            ),
            label='Results'
        )
        return grp

    def _query_edit_view(self):
        v = View(HGroup(
            UItem('parameter',
                  editor=EnumEditor(name='parameters')
            ),
            UItem('comparator',
                  editor=EnumEditor(name='comparisons')
            ),
            UItem('criterion'),
            UItem('criterion',
                  width=-25,
                  editor=EnumEditor(name='criteria')
            )

        ),
                 height=125
        )
        return v

    def _table_editor(self):
        cols = [
            CheckboxColumn(name='use', label='',
                           width=30),
            ObjectColumn(name='parameter',
                         editor=EnumEditor(name='parameters'),
                         label='Param.',
                         width=125
            ),
            ObjectColumn(name='comparator',
                         editor=EnumEditor(name='comparisons'),
                         label='',
                         width=50
            ),
            #                 ObjectColumn(name='criterion'),
            ObjectColumn(name='criterion',
                         editor=EnumEditor(name='criteria'),
                         label='Value',
                         width=125
            ),
        ]

        editor = TableEditor(columns=cols,
                             deletable=True,
                             show_toolbar=True,
                             sortable=False,
                             selected=selector_name('selected_query'),
                             #                              selection_mode='row',
                             edit_view=self._query_edit_view(),
                             #                              auto_size=True
                             row_factory=self.model.database_selector.query_factory,
                             #                              auto_add=True
        )

        return editor

    def _query_group(self):
        editor = self._table_editor()
        query_itm = Item(selector_name('queries'), show_label=False,
                         style='custom',
                         editor=editor,
                         #                                    editor=ListEditor(mutable=False,
                         #                                                   style='custom',
                         #                                                   editor=InstanceEditor()),
                         #                              height=0.25,
                         visible_when='kind=="Database"',
        )
        return query_itm

    def traits_view(self):
    #         editor = ListEditor(mutable=False,
    #                           style='custom',
    #                           editor=InstanceEditor())
    #
        grp = HGroup(
            UItem('kind'),
            UItem('open_button',
                  visible_when='kind=="File"'),
            UItem(selector_name('add_query_button'),
                  style='custom',
                  editor=ButtonEditor(label='',
                                      image=ImageResource(name='add.png',
                                                          search_path=paths.icon_search_path)),
                  visible_when='kind=="Database"'),
            UItem(selector_name('delete_query_button'),
                  style='custom',
                  editor=ButtonEditor(image=ImageResource(name='delete.png',
                                                          search_path=paths.icon_search_path)),
                  visible_when='kind=="Database"'))
        filter_grp = HGroup(
            UItem(selector_name('search'),
                  visible_when='kind=="Database"'),
            UItem(selector_name('mass_spectrometer'),
                  label='Spec.',
                  editor=EnumEditor(name=selector_name('mass_spectrometers'))),
            UItem(selector_name('analysis_type'),
                  editor=EnumEditor(name=selector_name('analysis_types'))),
            visible_when='kind=="Database"')

        results_grp=VSplit(self._results_group(),
                           VGroup(grp,filter_grp,self._query_group()))
        button_grp=HGroup(icon_button_editor('append_button','add', tooltip='Append'),
                          icon_button_editor('replace_button','arrow_refresh',tooltip='Replace'))
        v = View(VGroup(button_grp, results_grp))
        return v




#============= EOF =============================================

