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
import json
import urllib2
from envisage.ui.tasks.preferences_pane import PreferencesPane
from traits.api import Str, Bool, List
from traitsui.api import View, Item, EnumEditor, TextEditor, VGroup

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.tasks.base_preferences_helper import BasePreferencesHelper, remote_status_item, \
    GitRepoPreferencesHelper


class UpdatePreferencesHelper(GitRepoPreferencesHelper):
    preferences_path = 'pychron.update'
    check_on_startup = Bool(False)
    use_development = Bool(False)
    _branches = List

    def __init__(self, *args, **kw):
        super(UpdatePreferencesHelper, self).__init__(*args, **kw)
        if self.remote:
            self._connection_hook()

    def _get_branches(self, new):
        try:
            cmd = 'https://api.github.com/repos/{}/branches'.format(new)
            doc = urllib2.urlopen(cmd)
            bs = [branch['name'] for branch in json.load(doc)]
            return [bi for bi in bs if bi.startswith('release') or bi in ('develop','master')]
        except BaseException:
            return []

    def _connection_hook(self):
        # use github api to retrieve information
        self._branches = self._get_branches(self.remote)


class UpdatePreferencesPane(PreferencesPane):
    model_factory = UpdatePreferencesHelper
    category = 'Update'

    def traits_view(self):
        v = View(Item('check_on_startup', label='Check for updates at startup'),
                 VGroup(remote_status_item(),
                        Item('branch', editor=EnumEditor(name='_branches'), label='Branch'),
                        show_border=True,
                        label='Update Repo'))
        return v

# ============= EOF =============================================

