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
from traits.api import HasTraits, Str, Any
from traits.trait_types import Int
from traits.traits import Property
from traitsui.api import View, UItem, TextEditor, Item, VGroup
# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.tabular_adapter import TabularAdapter

from pychron.core.helpers.traitsui_shortcuts import okcancel_view


class StatusView(HasTraits):
    def traits_view(self):
        v = View(UItem('status', style='custom',
                       editor=TextEditor(read_only=True)),
                 kind='modal',
                 title='Repository Status',
                 width=500,
                 resizable=True)
        return v


class NewTagView(HasTraits):
    message = Str
    name = Str

    def traits_view(self):
        v = okcancel_view(VGroup(Item('name'),
                                 VGroup(UItem('message', style='custom'),
                                        show_border=True, label='Message')),
                          width=400,
                          title='New Tag')

        return v


class NewBranchView(HasTraits):
    name = Property(depends_on='_name')
    branches = Any
    _name = Str

    def traits_view(self):
        v = okcancel_view(UItem('name'),
                          width=200,
                          title='New Branch')
        return v

    def _get_name(self):
        return self._name

    def _set_name(self, v):
        self._name = v

    def _validate_name(self, v):
        if v not in self.branches:
            if ' ' not in v:
                return v


class GitObjectAdapter(TabularAdapter):
    hexsha_width = Int(80)
    message_width = Int(300)
    date_width = Int(120)

    font = '10'
    hexsha_text = Property
    message_text = Property

    def _get_hexsha_text(self):
        return self.item.hexsha[:8]

    def _get_message_text(self):
        return self._truncate_message(self.item.message)

    def _truncate_message(self, m):
        if len(m) > 200:
            m = '{}...'.format(m[:200])
        return m


class GitTagAdapter(GitObjectAdapter):
    columns = [('Name', 'name'),
               ('Message', 'message'),
               ('Date', 'date'),
               ('Commit', 'hexsha'),
               ('Commit Message', 'commit_message')]
    name_width = Int(60)
    commit_message_text = Property

    def _get_commit_message_text(self):
        return self._truncate_message(self.item.commit_message)


class CommitAdapter(GitObjectAdapter):
    columns = [('ID', 'hexsha'),
               ('Date', 'date'),
               ('Message', 'message'),
               ('Author', 'author'),
               ('Email', 'email'),
               ]
    author_width = Int(100)

# ============= EOF =============================================
