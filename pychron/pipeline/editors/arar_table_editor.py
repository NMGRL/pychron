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
from pyface.action.menu_manager import MenuManager
from traits.api import Property, List, cached_property, Str, Int
from traitsui.api import View, UItem, Item, VGroup, HGroup, Handler
from traitsui.menu import Action
# ============= standard library imports ========================
# ============= local library imports  ==========================

from pychron.column_sorter_mixin import ColumnSorterMixin
from pychron.pipeline.editors.base_adapter import BaseGroupAdapter, BaseAdapter
from pychron.processing.analyses.analysis_group import AnalysisGroup
from pychron.pipeline.editors.base_table_editor import BaseTableEditor
from pychron.core.ui.tabular_editor import myTabularEditor
from pychron.pychron_constants import PLUSMINUS_ONE_SIGMA


class ArArTableAdapter(BaseAdapter):
    columns = [
        ('RunID', 'record_id'),
        ('Tag', 'tag'),
        ('Table Group', 'table_group'),
        # ('Power', 'extract_value'),
        # ('Ar40', 'Ar40'),
        # (PLUSMINUS_ONE_SIGMA, 'Ar40_err'),
        #
        # ('Ar39', 'Ar39'),
        # (PLUSMINUS_ONE_SIGMA, 'Ar39_err'),
        #
        # ('Ar38', 'Ar38'),
        # (PLUSMINUS_ONE_SIGMA, 'Ar38_err'),
        #
        # ('Ar37', 'Ar37'),
        # (PLUSMINUS_ONE_SIGMA, 'Ar37_err'),
        #
        # ('Ar36', 'Ar36'),
        # (PLUSMINUS_ONE_SIGMA, 'Ar36_err'),
        # ('%40Ar*', 'rad40_percent'),
        #
        # #     ('40Ar*/39ArK', 'F'),
        ('Age', 'age'),
        (PLUSMINUS_ONE_SIGMA, 'age_err'),
        ('K/Ca', 'kca'),
        # (PLUSMINUS_ONE_SIGMA, 'kca_err'),
        #     ('', 'blank_column')
    ]

    table_group_text = Property
    record_id_width = Int(60)

    def _get_table_group_text(self):
        ret = ''
        if hasattr(self.item, 'table_group'):
            ret = self.item.table_group
        return ret

    def get_menu(self, obj, trait, row, column):
        m = MenuManager(Action(name='Calculate Mean', action='group_as_weighted_mean'),
                        Action(name='Calculate Plateau', action='group_as_plateau'),
                        Action(name='Calculate Isochron', action='group_as_isochron'))
        return m


class GroupTableAdapter(BaseGroupAdapter):
    pass


class THandler(Handler):
    def group_as_weighted_mean(self, info, obj):
        obj.group_as_weighted_mean()
        obj.refresh_needed = True

    def group_as_plateau(self, info, obj):
        obj.group_as_plateau()
        obj.refresh_needed = True

    def group_as_isochron(self, info, obj):
        obj.group_as_isochron()
        obj.refresh_needed = True


class ArArTableEditor(BaseTableEditor, ColumnSorterMixin):
    analysis_groups = Property(List, depends_on='items[]')
    # pdf_writer_klass = None
    # xls_writer_klass = None
    # csv_writer_klass = None

    analysis_group_klass = AnalysisGroup
    adapter_klass = ArArTableAdapter
    analysis_groups_adapter_klass = GroupTableAdapter

    help_str = Str('Right-click to subgroup analyses and calculate an age')

    def group_as_plateau(self):
        self._group('plateau')

    def group_as_weighted_mean(self):
        self._group('weighted_mean')

    def group_as_isochron(self):
        self._group('isochron')

    def _group(self, tag):
        gs = {r.table_grouping for r in self.items if hasattr(r, 'table_grouping')}
        gs = [int(gi.split('_')[-1]) for gi in gs]
        table_grouping_cnt = max(gs) if gs else -1

        for s in self.selected:
            s.table_group = '{}_{}'.format(tag, table_grouping_cnt + 1)

    def traits_view(self):
        v = View(VGroup(
            HGroup(UItem('help_str', style='readonly'),
                   show_border=True, label='Info'),
            UItem('items',
                  editor=myTabularEditor(adapter=self.adapter_klass(),
                                         # col_widths='col_widths',
                                         selected='selected',
                                         multi_select=True,
                                         auto_update=False,
                                         refresh='refresh_needed',
                                         operations=['delete', 'move'],
                                         column_clicked='column_clicked')),
            # UItem('analysis_groups',
            #       editor=myTabularEditor(adapter=self.analysis_groups_adapter_klass(),
            #                              #                                              auto_resize=True,
            #                              editable=False,
            #                              auto_update=False,
            #                              refresh='refresh_needed'))
        ),
            handler=THandler())
        return v

        # ============= EOF =============================================
