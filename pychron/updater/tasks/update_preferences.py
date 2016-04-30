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
from traits.api import Str, Bool, List
from traitsui.api import View, Item, EnumEditor, VGroup


# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.tasks.base_preferences_helper import remote_status_item, \
    GitRepoPreferencesHelper
from pychron.pychron_constants import LINE_STR


class UpdatePreferencesHelper(GitRepoPreferencesHelper):
    preferences_path = 'pychron.update'
    check_on_startup = Bool(False)

    use_tag = Bool
    version_tag = Str

    branch = Str
    _branches = List
    _tags = List

    def __init__(self, *args, **kw):
        super(UpdatePreferencesHelper, self).__init__(*args, **kw)
        if self.remote:
            self._connection_hook()

    def _get_branches_tags(self, new):
        try:
            # cmd = 'https://api.github.com/repos/{}/branches'.format(new)
            # doc = urllib2.urlopen(cmd)
            # bs = [branch['name'] for branch in json.load(doc)]
            from pychron.github import get_branches, get_tags

            bs = get_branches(new)
            from git import Repo
            from pychron.paths import paths

            remotes = [bi for bi in bs if bi.startswith('release') or bi in ('develop', 'master')]

            localbranches = []
            if os.path.isdir(os.path.join(paths.build_repo, '.git')):
                repo = Repo(paths.build_repo)
                localbranches = [b.name for b in repo.branches if b.name not in remotes]

            if localbranches:
                remotes.append(LINE_STR)
                remotes.extend(localbranches)

            tags = [t for t in get_tags(new) if t.startswith('rc')]
            print remotes, tags
            return remotes, tags

        except BaseException, e:
            import traceback
            traceback.print_exc()
            return [], []

    def _connection_hook(self):
        # use github api to retrieve information
        self._branches, self._tags = self._get_branches_tags(self.remote)


class UpdatePreferencesPane(PreferencesPane):
    model_factory = UpdatePreferencesHelper
    category = 'Update'

    def traits_view(self):
        v = View(VGroup(Item('check_on_startup',
                             label='Check for updates at startup'),
                        VGroup(remote_status_item(),
                               Item('use_tag', label='Use Production'),
                               Item('version_tag', editor=EnumEditor(name='_tags')),
                               Item('branch', editor=EnumEditor(name='_branches'),
                                    enabled_when='not use_tag',
                                    label='Branch'),
                               show_border=True,
                               label='Update Repo'),
                        label='Update',
                        show_border=True))
        return v

# ============= EOF =============================================

