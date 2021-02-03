# ===============================================================================
# Copyright 2015 Jake Ross
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
from pyface.tasks.traits_dock_pane import TraitsDockPane
from pyface.tasks.traits_task_pane import TraitsTaskPane
from traits.api import Property, Int
from traitsui.api import View, UItem, VGroup, TabularEditor, EnumEditor, VSplit, Item, HSplit, HGroup, Tabbed
from traitsui.editors import ListStrEditor
from traitsui.tabular_adapter import TabularAdapter

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.helpers.datetime_tools import ISO_FORMAT_STR
from pychron.core.pychron_traits import BorderVGroup
from pychron.core.ui.dag_editor import GitDAGEditor
from pychron.git_archive.views import GitTagAdapter, TopologyAdapter, DiffsAdapter
from pychron.pychron_constants import NULL_STR


class RepoCentralPane(TraitsTaskPane):
    def traits_view(self):
        dag_grp = UItem('commits', editor=GitDAGEditor(selected='selected'))
        commit_grp = VGroup(HGroup(Item('ncommits', label='Limit'),
                                   Item('use_simplify_dag', label='Simplify')),
                            BorderVGroup(UItem('commits',
                                               editor=TabularEditor(adapter=TopologyAdapter(),
                                                                    scroll_to_row='scroll_to_row',
                                                                    selected='selected_commit')),
                                         label='Commits'))
        commit_grp = HSplit(commit_grp, dag_grp)

        bookmark_grp = VGroup(BorderVGroup(UItem('git_tags', editor=TabularEditor(adapter=GitTagAdapter()),
                                                 height=200), label='Bookmarks'))

        file_grp = VGroup(HGroup(Tabbed(UItem('diffs',
                                              label='Diffs',
                                              editor=TabularEditor(adapter=DiffsAdapter(),
                                                                   editable=False)),
                                        UItem('diff_text',
                                              label='Text',
                                              style='custom')),
                                 UItem('files', style='custom',
                                       editor=ListStrEditor(selected='selected_file',
                                                            editable=False))), label='Files')
        a_grp = VGroup(UItem('analyses', style='custom', editor=ListStrEditor(editable=False)), label='Analyses')

        v = View(VGroup(UItem('branch',
                              editor=EnumEditor(name='branches')),
                        VSplit(commit_grp, HSplit(bookmark_grp, Tabbed(a_grp, file_grp)))))
        return v


class RepoAdapter(TabularAdapter):
    columns = [('Name', 'name'),
               ('Branch', 'active_branch'),
               ('Status (Ahead,Behind)', 'status')]

    name_width = Int(180)
    active_branch_width = Int(100)
    status = Int(100)

    # name_text = Property
    # def _get_name_text(self):
    #     return '{} ({})'.format(self.item.name, self.item.active_branch)

    def get_bg_color(self, obj, trait, row, column=0):
        item = getattr(obj, trait)[row]
        color = 'white'
        if item.dirty:
            color = 'red'
        return color


class OriginAdapter(TabularAdapter):
    columns = [('Name', 'name'),
               ('Created', 'create_date'),
               ('Last Commit', 'push_date')]
    create_date_text = Property
    push_date_text = Property

    def _get_create_date_text(self):
        d = self.item.create_date
        if d != NULL_STR:
            d = d.strftime(ISO_FORMAT_STR)
        return d

    def _get_push_date_text(self):
        d = self.item.push_date
        if d != NULL_STR:
            d = d.strftime(ISO_FORMAT_STR)
        return d


class SelectionPane(TraitsDockPane):
    id = 'pychron.repo.selection'
    name = 'Repositories'

    def traits_view(self):
        origin_grp = BorderVGroup(UItem('filter_origin_value',
                                        tooltip='Fuzzy filter list of repositories available at "Origin". '
                                                'e.g. "foo" will match "foo", "foobar", "fobaro", "barfoo", etc'),
                                  UItem('repository_names',
                                        editor=TabularEditor(selected='selected_repository',
                                                             column_clicked='origin_column_clicked',
                                                             adapter=OriginAdapter(),
                                                             editable=False)),
                                  label='Origin')

        local_grp = BorderVGroup(UItem('filter_repository_value',
                                       tooltip='Fuzzy filter list of repositories available at on this computer. '
                                               'e.g. "foo" will match "foo", "foobar", "fobaro", "barfoo", etc'),
                                 UItem('local_names',
                                       editor=TabularEditor(adapter=RepoAdapter(),
                                                            column_clicked='column_clicked',
                                                            selected='selected_local_repositories',
                                                            editable=False,
                                                            multi_select=True,
                                                            stretch_last_section=False
                                                            )),
                                 label='Local')

        v = View(VGroup(local_grp, origin_grp))
        return v

# ============= EOF =============================================
