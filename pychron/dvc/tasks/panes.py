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
from traits.api import Property
from traitsui.api import View, UItem, VGroup, TabularEditor, EnumEditor, VSplit, Item
from traitsui.tabular_adapter import TabularAdapter

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.helpers.datetime_tools import ISO_FORMAT_STR
from pychron.git_archive.views import CommitAdapter, GitTagAdapter


class RepoCentralPane(TraitsTaskPane):
    def traits_view(self):
        commit_grp = VGroup(Item('ncommits', label='Limit'),
                            VGroup(UItem('commits',
                                         editor=TabularEditor(adapter=CommitAdapter(),
                                                              selected='selected_commit')),
                                   show_border=True, label='Commits'))
        bookmark_grp = VGroup(VGroup(UItem('git_tags', editor=TabularEditor(adapter=GitTagAdapter()),
                                           height=200),
                                     show_border=True, label='Bookmarks'))

        v = View(VGroup(UItem('branch',
                              editor=EnumEditor(name='branches')),
                        VSplit(commit_grp, bookmark_grp)))
        return v


class RepoAdapter(TabularAdapter):
    columns = [('Name', 'name'),
               ('Branch', 'active_branch'),
               ('Status (Ahead,Behind)', 'status')]

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
        return self.item.create_date.strftime(ISO_FORMAT_STR)

    def _get_push_date_text(self):
        return self.item.push_date.strftime(ISO_FORMAT_STR)


class SelectionPane(TraitsDockPane):
    id = 'pychron.repo.selection'
    name = 'Repositories'

    def traits_view(self):
        origin_grp = VGroup(UItem('filter_origin_value',
                                  tooltip='Fuzzy filter list of repositories available at "Origin". '
                                          'e.g. "foo" will match "foo", "foobar", "fobaro", "barfoo", etc'),
                            UItem('repository_names',
                                  editor=TabularEditor(selected='selected_repository',
                                                       column_clicked='origin_column_clicked',
                                                       adapter=OriginAdapter(),
                                                       editable=False)),
                            show_border=True, label='Origin')

        local_grp = VGroup(UItem('filter_repository_value',
                                 tooltip='Fuzzy filter list of repositories available at on this computer. '
                                         'e.g. "foo" will match "foo", "foobar", "fobaro", "barfoo", etc'),
                           UItem('local_names',
                                 editor=TabularEditor(adapter=RepoAdapter(),
                                                      column_clicked='column_clicked',
                                                      selected='selected_local_repositories',
                                                      editable=False,
                                                      multi_select=True,
                                                      )),
                           show_border=True, label='Local')

        v = View(VGroup(local_grp, origin_grp))
        return v

# ============= EOF =============================================
