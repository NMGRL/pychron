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
import os

from envisage.ui.tasks.preferences_pane import PreferencesPane
from git import Repo
from git.exc import InvalidGitRepositoryError
from pyface.message_dialog import warning
from traits.api import Str, Bool, List, Button, Instance
from traitsui.api import View, Item, EnumEditor, VGroup, HGroup

from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.envisage.tasks.base_preferences_helper import remote_status_item, \
    GitRepoPreferencesHelper
from pychron.paths import build_repo
from pychron.pychron_constants import LINE_STR


class Updater:
    _repo = None

    def pull(self, branch, inform=False):
        repo = self._get_working_repo(inform)
        origin = repo.remote('origin')
        origin.pull(branch)

    def checkout_branch(self, name, inform=False):
        repo = self._get_working_repo(inform)
        try:
            branch = getattr(repo.branches, name)
        except AttributeError:
            if name.startswith('origin'):
                name = '/'.join(name.split('/')[1:])
            branch = repo.create_head(name)

        branch.checkout()

    def checkout_tag(self, tag, inform=False):
        repo = self._get_working_repo(inform)
        if repo:
            try:
                branch = getattr(repo.branches, tag)
                branch.checkout()
            except AttributeError:
                repo.git.fetch()
                repo.git.checkout('-b', tag, tag)

    def _get_working_repo(self, inform):
        if not self._repo:
            try:
                self._repo = Repo(build_repo)
            except InvalidGitRepositoryError:
                if inform:
                    warning(None, 'Invalid Build repository {}.\n'
                                  'Pychron not properly configured for update. \n\n'
                                  'Contact developer'.format(build_repo))
        return self._repo


class UpdatePreferencesHelper(GitRepoPreferencesHelper):
    preferences_path = 'pychron.update'
    check_on_startup = Bool(False)

    use_tag = Bool
    version_tag = Str

    branch = Str

    checkout_branch_button = Button
    pull_button = Button

    _branches = List
    _tags = List

    _updater = Instance(Updater, ())
    _initialized = False

    def __init__(self, *args, **kw):
        super(UpdatePreferencesHelper, self).__init__(*args, **kw)
        if self.remote:
            self._connection_hook()

    def _get_branches_tags(self, new):
        try:
            from pychron.github import get_branches, get_tags

            bs = get_branches(new)

            remotes = [bi for bi in bs if bi.startswith('release') or bi in ('develop', 'master')]

            localbranches = []
            if os.path.isdir(os.path.join(build_repo, '.git')):
                repo = Repo(build_repo)
                localbranches = [b.name for b in repo.branches if b.name not in remotes]

            if localbranches:
                remotes.append(LINE_STR)
                remotes.extend(localbranches)

            tags = [t for t in get_tags(new) if t.startswith('rc')]
            return remotes, tags

        except BaseException, e:
            import traceback
            traceback.print_exc()
            return [], []

    def _connection_hook(self):
        # use github api to retrieve information
        self._branches, self._tags = self._get_branches_tags(self.remote)

    def _use_tag_changed(self, name, old, new):
        if not self.use_tag:
            if self.branch:
                self._updater.checkout_branch(self.branch, inform=self._initialized)
                self._initialized = True
        else:
            self._version_tag_changed()

    def _version_tag_changed(self):
        if self.use_tag and self.version_tag:
            self._updater.checkout_tag(self.version_tag, inform=self._initialized)
            self._initialized = True

    def _checkout_branch_button_fired(self):
        self._updater.checkout_branch(self.branch, inform=self._initialized)

    def _pull_button_fired(self):
        self._updater.pull(self.branch, inform=self._initialized)


class UpdatePreferencesPane(PreferencesPane):
    model_factory = UpdatePreferencesHelper
    category = 'Update'

    def traits_view(self):
        v = View(VGroup(Item('check_on_startup',
                             label='Check for updates at startup'),
                        VGroup(remote_status_item(),
                               Item('use_tag', label='Use Production'),
                               Item('version_tag', editor=EnumEditor(name='_tags'),
                                    enabled_when='use_tag'),
                               Item('branch', editor=EnumEditor(name='_branches'),
                                    enabled_when='not use_tag',
                                    label='Branch'),
                               HGroup(icon_button_editor('checkout_branch_button', 'bricks',
                                                         tooltip='Checkout selected branch'),
                                      icon_button_editor('pull_button', 'arrow_down',
                                                         tooltip='Update Branch'),
                                      enabled_when='not use_tag'),
                               show_border=True,
                               label='Update Repo'),
                        label='Update',
                        show_border=True))
        return v

# ============= EOF =============================================
