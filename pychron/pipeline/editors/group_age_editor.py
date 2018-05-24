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
from pychron.pipeline.subgrouping import apply_subgrouping, compress_groups, set_subgrouping_error
from pychron.pychron_constants import PLUSMINUS_ONE_SIGMA, MSEM, SEM, SD


# ============= standard library imports ========================
# ============= local library imports  ==========================


class GroupAgeAdapter(BaseAdapter):
    columns = [
        ('RunID', 'record_id'),
        ('Tag', 'tag'),
        ('Group', 'group_id'),
        ('SubGroup', 'subgroup'),
        ('Kind', 'kind'),
        ('Error', 'error_kind'),

        ('Age', 'age'),
        (PLUSMINUS_ONE_SIGMA, 'age_err'),
        ('K/Ca', 'kca')]

    subgroup_text = Property
    record_id_width = Int(60)
    tag_width = Int(40)
    group_id_width = Int(60)
    subgroup_width = Int(100)

    kind_text = Property
    error_kind_text = Property

    def _get_subgroup_text(self):
        return self._get_subgroup_attr('name')

    def _get_kind_text(self):
        return self._get_subgroup_attr('kind')

    def _get_error_kind_text(self):
        return self._get_subgroup_attr('error_kind')

    def _get_subgroup_attr(self, attr):
        ret = ''
        if self.item.subgroup:
            ret = self.item.subgroup[attr]
        return ret

    def get_menu(self, obj, trait, row, column):
        age = MenuManager(Action(name='Calculate Mean', action='group_as_weighted_mean'),
                          Action(name='Calculate Plateau', action='group_as_plateau'),
                          Action(name='Calculate Isochron', action='group_as_isochron'),
                          name='Age')

        error = MenuManager(Action(name=SD, action='group_sd'),
                            Action(name=SEM, action='group_sem'),
                            Action(name=MSEM, action='group_msem'),
                            name='Error')
        m = MenuManager(age,
                        error,
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

    def group_sd(self, info, obj):
        obj.group_sd()

    def group_sem(self, info, obj):
        obj.group_sem()

    def group_msem(self, info, obj):
        obj.group_msem()


class GroupAgeEditor(BaseTableEditor, ColumnSorterMixin):
    adapter_klass = GroupAgeAdapter

    help_str = Str('Right-click to subgroup analyses and calculate an age')

    def clear_grouping(self):
        if self.selected:
            for s in self.selected:
                s.subgroup = None

            compress_groups(self.items)

    def group_sd(self):
        self._group_error(SD)

    def group_sem(self):
        self._group_error(SEM)

    def group_msem(self):
        self._group_error(MSEM)

    def group_as_plateau(self):
        self._group('plateau')

    def group_as_weighted_mean(self):
        self._group('weighted_mean')

    def group_as_isochron(self):
        self._group('isochron')

    def _group_error(self, tag):
        if self.selected:
            set_subgrouping_error(tag, self.selected, self.items)
            self.refresh_needed = True

    def _group(self, tag):
        if self.selected:
            apply_subgrouping(tag, MSEM, self.selected, items=self.items)
            self.refresh_needed = True

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
