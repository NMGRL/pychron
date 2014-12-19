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
from traits.api import HasTraits, Button, Str, Int, Property
from traitsui.api import View, Item, VGroup, UItem, HGroup, VSplit, InstanceEditor
# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.editors import TabularEditor
from traitsui.handler import Controller
from traitsui.item import Readonly
from traitsui.tabular_adapter import TabularAdapter
from pychron.git_archive.history import CommitAdapter, BaseGitHistory


class UpdateGitHistory(BaseGitHistory):
    local_commit = Str
    latest_remote_commit = Str
    n = Int
    branchname = Str


class CommitAdapter(TabularAdapter):
    columns = [('Message', 'message'),
               ('Date', 'date'),
               ('SHA','hexsha')]
    message_width = Int(500)
    hexsha_text = Property
    def _get_hexsha_text(self):
        return self.item.hexsha[:10]

class CommitView(Controller):
    model = BaseGitHistory

    def traits_view(self):
        v = View(
                 HGroup(
                     Readonly('local_commit',label='Your Version'),
                     Readonly('latest_remote_commit',label='Latest Version'),
                     Readonly('n', label='Commits Behind')),
                 UItem('items',
                       editor=TabularEditor(adapter=CommitAdapter(),
                                            selected='selected')),
                 kind='livemodal',
                 width=800,
                 height=400,
                 buttons=['OK','Cancel'],
                 title='Available Updates- Branch= {}'.format(self.model.branchname),
                 resizable=True)
        return v

# ============= EOF =============================================



