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
from traits.api import Str, Int, Property, List
from traitsui.api import View, VGroup, UItem, HGroup, Group, Tabbed
# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.editors import TabularEditor
from traitsui.handler import Controller
from traitsui.item import Readonly
from traitsui.tabular_adapter import TabularAdapter
from pychron.git_archive.history import CommitAdapter, BaseGitHistory
from pychron.pychron_constants import LIGHT_YELLOW


class UpdateGitHistory(BaseGitHistory):
    local_commit = Str
    latest_remote_commit = Str
    n = Int
    branchname = Str
    tags = List

    def set_tags(self, tags):
        gfactory = self.git_sha_object_factory
        def factory(t):
            obj = gfactory(t.commit)
            obj.name = t.name
            return obj

        self.tags = sorted([factory(ti) for ti in tags], key=lambda x: x.date,
                           reverse=True)


class CommitAdapter(TabularAdapter):
    columns = [('Message', 'message'),
               ('Date', 'date'),
               ('SHA', 'hexsha')]
    message_width = Int(500)
    date_width = Int(185)
    hexsha_text = Property

    def _get_hexsha_text(self):
        return self.item.hexsha[:10]

    def get_bg_color(self, obj, trait, row, column=0):
        item = getattr(obj, trait)[row]
        return LIGHT_YELLOW if item.active else 'white'


class TagAdapter(CommitAdapter):
    columns = [('Tag','name'),
               ('Message', 'message'),
               ('Date', 'date'),
               ('SHA', 'hexsha')]
    name_width = Int(100)

class BaseCommitsView(Controller):
    model = BaseGitHistory

    def traits_view(self):
        v = View(VGroup(*self._groups()),
                 kind='livemodal',
                 width=900,
                 height=400,
                 buttons=['OK', 'Cancel'],
                 title='Available Updates- Branch= {}'.format(self.model.branchname),
                 resizable=True)
        return v

    def _groups(self):
        raise NotImplementedError

    def _items_grp(self):
        return UItem('items',
                     editor=TabularEditor(adapter=CommitAdapter(),
                                          editable=False,
                                          selected='selected'))

    def _info_grp(self):
        return HGroup(
            Readonly('local_commit', label='Your Version'),
            Readonly('latest_remote_commit', label='Latest Version'),
            Readonly('n', label='Commits Behind',
                     visible_when='show_behind'))


class ManageCommitsView(BaseCommitsView):
    def _groups(self):
        igrp = Group(self._items_grp(), label='Commits')
        tgrp = VGroup(UItem('tags', editor=TabularEditor(adapter=TagAdapter(),
                                                         editable=False,
                                                         selected='selected')),
                      label='Tags')
        return [self._info_grp(), Tabbed(tgrp, igrp)]


class CommitView(BaseCommitsView):
    def _groups(self):
        return [self._info_grp(), self._items_grp()]
        # def traits_view(self):
        # v = View(,
        # UItem('items',
        # editor=TabularEditor(adapter=CommitAdapter(),
        #                                         editable=False,
        #                                         selected='selected')),
        #              kind='livemodal',
        #              width=900,
        #              height=400,
        #              buttons=['OK', 'Cancel'],
        #              title='Available Updates- Branch= {}'.format(self.model.branchname),
        #              resizable=True)
        #     return v

# ============= EOF =============================================



