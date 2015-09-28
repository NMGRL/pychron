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
from traits.api import Instance
from traitsui.api import View, Item, UItem, VGroup, HGroup
from traitsui.editors import TableEditor, TabularEditor
from traitsui.extras.checkbox_column import CheckboxColumn

from traitsui.handler import Controller
from traitsui.table_column import ObjectColumn
from traitsui.tabular_adapter import TabularAdapter

# ============= standard library imports ========================

# ============= local library imports  ==========================

# ============= EOF =============================================
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.pipeline.tagging.analysis_tags import AnalysisTagModel
from pychron.pipeline.tagging.data_reduction_tags import DataReductionTagModel, SelectDataReductionTagModel


class DataReductionItemAdapter(TabularAdapter):
    columns = [('Name', 'name'),
               ('Date', 'create_date'),
               ('User', 'user'),
               ('Comment', 'comment')]


class SelectDataReductionTagView(Controller):
    model = Instance(SelectDataReductionTagModel)

    def traits_view(self):
        v = View(HGroup(Item('name_filter', label='Name'),
                        Item('user_filter', label='User')),
                 UItem('tags',
                       editor=TabularEditor(adapter=DataReductionItemAdapter(),
                                            editable=False,
                                            selected='selected')),
                 buttons=['OK', 'Cancel'],
                 width=500,
                 kind='livemodal',
                 resizable=True,
                 title='Select Data Reduction Tag')
        return v


class ItemAdapter(TabularAdapter):
    columns = [('Run ID', 'record_id'),
               ('Sample', 'sample'),
               ('Tag', 'tag')]
    font = 'arial 10'


class DataReductionTagView(Controller):
    model = Instance(DataReductionTagModel)

    def traits_view(self):
        table = UItem('items', editor=TabularEditor(adapter=ItemAdapter(),
                                                    multi_select=True,
                                                    operations=['delete']))
        tag = HGroup(Item('tagname', label='Tag'),
                     UItem('edit_comment_button'))

        v = View(VGroup(tag, table),
                 resizable=True,
                 width=500,
                 height=400,
                 buttons=['OK', 'Cancel'],
                 kind='livemodal', title='Data Reduction Tagging')
        return v


class AnalysisTagView(Controller):
    model = Instance(AnalysisTagModel)

    def closed(self, info, isok):
        if isok:
            self.model.save()

    def traits_view(self):
        cols = [ObjectColumn(name='name', editable=False),
                # ObjectColumn(name='user', editable=False),
                CheckboxColumn(name='omit_ideo'),
                CheckboxColumn(name='omit_spec'),
                CheckboxColumn(name='omit_iso'),
                CheckboxColumn(name='omit_series')]

        editor = TableEditor(columns=cols,
                             selected='selected',
                             sortable=False, )

        v = View(UItem('tags',
                       editor=editor),
                 HGroup(
                     icon_button_editor('add_tag_button', 'add', tooltip='Add a tag'),
                     icon_button_editor('delete_tag_button', 'delete', tooltip='Delete selected tags'),
                     icon_button_editor('save_button', 'database_save',
                                        tooltip='Save changes from the "Tag" table to the database')),
                 UItem('items', editor=TabularEditor(adapter=ItemAdapter(),
                                                     multi_select=True,
                                                     operations=['delete']),
                       defined_when='items'),
                 HGroup(Item('use_filter', label='Remove "Invalid" analyses from figure'),
                        defined_when='items'),

                 resizable=True,
                 width=500,
                 height=400,
                 buttons=['OK', 'Cancel'],
                 kind='livemodal',
                 title='Tags')

        return v


if __name__ == '__main__':
    drv = DataReductionTagView(model=DataReductionTagModel())
    drv.configure_traits()
