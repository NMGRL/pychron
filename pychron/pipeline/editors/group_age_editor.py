# ===============================================================================
# Copyright 2018 ross
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
from pyface.action.menu_manager import MenuManager
from traits.api import Property, Str, Int
from traitsui.api import View, UItem, VGroup, HGroup, Handler
from traitsui.menu import Action

from pychron.column_sorter_mixin import ColumnSorterMixin
from pychron.core.ui.tabular_editor import myTabularEditor
from pychron.pipeline.editors.base_adapter import BaseAdapter
from pychron.pipeline.editors.base_table_editor import BaseTableEditor
from pychron.pipeline.tagging import apply_subgrouping, compress_groups
from pychron.pychron_constants import PLUSMINUS_ONE_SIGMA


# ============= standard library imports ========================
# ============= local library imports  ==========================


class GroupAgeAdapter(BaseAdapter):
    columns = [
        ('RunID', 'record_id'),
        ('Tag', 'tag'),
        ('Group', 'group_id'),
        ('SubGroup', 'subgroup'),
        ('Age', 'age'),
        (PLUSMINUS_ONE_SIGMA, 'age_err'),
        ('K/Ca', 'kca')]

    subgroup_text = Property
    record_id_width = Int(60)
    tag_width = Int(40)
    group_id_width = Int(60)
    subgroup_width = Int(100)

    def _get_subgroup_text(self):
        ret = self.item.subgroup or ''
        if ':' in ret:
            _, ret = ret.split(':')
        return ret

    def get_menu(self, obj, trait, row, column):
        m = MenuManager(Action(name='Calculate Mean', action='group_as_weighted_mean'),
                        Action(name='Calculate Plateau', action='group_as_plateau'),
                        Action(name='Calculate Isochron', action='group_as_isochron'),
                        Action(name='Clear Grouping', action='clear_grouping'))
        return m


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

    def clear_grouping(self, info, obj):
        obj.clear_grouping()


class GroupAgeEditor(BaseTableEditor, ColumnSorterMixin):
    adapter_klass = GroupAgeAdapter

    help_str = Str('Right-click to subgroup analyses and calculate an age')

    def clear_grouping(self):
        if self.selected:
            for s in self.selected:
                s.subgroup = ''

            compress_groups(self.items)

    def group_as_plateau(self):
        self._group('plateau')

    def group_as_weighted_mean(self):
        self._group('weighted_mean')

    def group_as_isochron(self):
        self._group('isochron')

    def _group(self, tag):
        if self.selected:
            apply_subgrouping(tag, self.selected, items=self.items)

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
                                         column_clicked='column_clicked'))),
            handler=THandler())
        return v

# ============= EOF =============================================
