# ===============================================================================
# Copyright 2021 ross
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
from traits.api import HasTraits, List, Str, Instance
from traitsui.api import View, EnumEditor, Item, VGroup, Label, UReadonly, TabularEditor, UItem, HGroup

from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.core.pychron_traits import BorderVGroup
from pychron.git_archive.repo_manager import GitRepoManager
from pychron.git_archive.views import CommitAdapter


class BranchMergeView(HasTraits):
    branches = List
    to_ = Str
    from_ = Str
    repo = Instance(GitRepoManager)

    from_changes = List
    to_changes = List

    to_label = Str
    from_label = Str
    msg = Str

    def _from__changed(self, new):
        # get the number of changes on from that are not on to_
        # also get the number of changes on to_ that are not on from

        cs = self.repo.get_branch_diff(self.from_, self.to_)
        self.to_changes = cs

        cs = self.repo.get_branch_diff(self.to_, self.from_)
        self.from_changes = cs

        bfrom = '<b>{}</b>'.format(self.from_)
        tfrom = '<b>{}</b>'.format(self.to_)
        fmt = 'Changes on {} but not on {}. n={}'
        self.from_label = fmt.format(bfrom, tfrom, len(self.from_changes))
        self.to_label = fmt.format(tfrom, bfrom, len(self.to_changes))

        if not self.from_changes:
            self.msg = '{}. Fully merged'.format(self.to_)
        else:
            self.msg = self.to_

    def traits_view(self):
        v = okcancel_view(VGroup(HGroup(Item('from_', editor=EnumEditor(name='branches')),
                                        Label('Into'),
                                        UReadonly('msg')),
                                 BorderVGroup(
                                     UReadonly('from_label'),
                                     UItem('from_changes', editor=TabularEditor(adapter=CommitAdapter()))),
                                 BorderVGroup(
                                     UReadonly('to_label'),
                                     UItem('to_changes', editor=TabularEditor(adapter=CommitAdapter()))),
                                 ),
                          title='Merge Branches'
                          )
        return v
# ============= EOF =============================================
